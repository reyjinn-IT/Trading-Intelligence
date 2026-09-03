const PAIR = "btc_idr";
let currentTimeframe = "1h";

let chart = null;
let candleSeries = null;
let ema18Series = null;
let ema50Series = null;
let poiPriceLine = null;
let cutLossPriceLine = null;

let currentCandles = [];
let currentEvaluation = null;

document.addEventListener("DOMContentLoaded", () => {
    initChart();
    setupEventListeners();
    loadAllData();
    setInterval(fetchTicker, 5000);
});

function initChart() {
    const container = document.getElementById("chartContainer");
    if (!container || typeof LightweightCharts === "undefined") return;

    container.innerHTML = "";

    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: container.clientHeight || 480,
        layout: {
            background: { type: 'solid', color: '#121316' },
            textColor: '#8B8D93',
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 11,
        },
        grid: {
            vertLines: { color: '#1C1D21' },
            horzLines: { color: '#1C1D21' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: {
                color: 'rgba(139, 141, 147, 0.4)',
                width: 1,
                style: 3,
                labelBackgroundColor: '#1E1F24',
            },
            horzLine: {
                color: 'rgba(139, 141, 147, 0.4)',
                width: 1,
                style: 3,
                labelBackgroundColor: '#1E1F24',
            },
        },
        rightPriceScale: {
            borderColor: '#232428',
            scaleMargins: { top: 0.1, bottom: 0.1 },
        },
        timeScale: {
            borderColor: '#232428',
            timeVisible: true,
            secondsVisible: false,
        },
    });

    candleSeries = chart.addCandlestickSeries({
        upColor: '#26A69A',
        downColor: '#EF5350',
        borderVisible: false,
        wickUpColor: '#26A69A',
        wickDownColor: '#EF5350',
        priceFormat: {
            type: 'custom',
            formatter: (price) => 'Rp ' + parseInt(price).toLocaleString(),
        },
    });

    ema18Series = chart.addLineSeries({
        color: '#38BDF8',
        lineWidth: 1.5,
        priceLineVisible: false,
        lastValueVisible: false,
    });

    ema50Series = chart.addLineSeries({
        color: '#F59E0B',
        lineWidth: 1.5,
        priceLineVisible: false,
        lastValueVisible: false,
    });

    const resizeObserver = new ResizeObserver((entries) => {
        if (!entries || entries.length === 0 || !chart) return;
        const { width, height } = entries[0].contentRect;
        chart.applyOptions({ width, height: height || 480 });
    });
    resizeObserver.observe(container);
}

function setupEventListeners() {
    const btnSync = document.getElementById("btnSync");
    if (btnSync) {
        btnSync.addEventListener("click", () => loadAllData());
    }

    document.querySelectorAll(".tf-item, .tf-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".tf-item, .tf-btn").forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            currentTimeframe = e.target.dataset.tf;
            loadKlinesAndEvaluation();
        });
    });
}

async function loadAllData() {
    await Promise.all([
        fetchTicker(),
        loadKlinesAndEvaluation()
    ]);
}

async function fetchTicker() {
    try {
        const res = await fetch(`/api/ticker?pair=${PAIR}`);
        if (!res.ok) return;
        const data = await res.json();
        renderTicker(data);
    } catch (e) {
        console.warn("Ticker error:", e);
    }
}

function renderTicker(t) {
    if (!t) return;
    const topLast = document.getElementById("topLastPrice");
    const topHigh = document.getElementById("topHigh");
    const topLow = document.getElementById("topLow");
    const topVol = document.getElementById("topVolIdr");

    if (topLast) topLast.textContent = `Rp ${parseInt(t.last).toLocaleString()}`;
    if (topHigh) topHigh.textContent = `Rp ${parseInt(t.high).toLocaleString()}`;
    if (topLow) topLow.textContent = `Rp ${parseInt(t.low).toLocaleString()}`;
    if (topVol) {
        const volMiliar = (t.vol_idr / 1e9).toFixed(2);
        topVol.textContent = `Rp ${volMiliar} Miliar`;
    }
}

async function loadKlinesAndEvaluation() {
    try {
        const [klinesRes, evalRes] = await Promise.all([
            fetch(`/api/klines?pair=${PAIR}&timeframe=${currentTimeframe}&limit=1500`),
            fetch(`/api/evaluate?pair=${PAIR}&timeframe=${currentTimeframe}`)
        ]);

        if (klinesRes.ok) {
            currentCandles = await klinesRes.json();
            renderChartData(currentCandles);
        }

        if (evalRes.ok) {
            currentEvaluation = await evalRes.json();
            renderEvaluation(currentEvaluation);
            renderPriceLines(currentEvaluation);
        }
    } catch (e) {
        console.warn("Klines and eval error:", e);
    }
}

function renderChartData(candles) {
    if (!candleSeries || !Array.isArray(candles) || candles.length === 0) return;

    const cData = [];
    const ema18Data = [];
    const ema50Data = [];
    const seenTimes = new Set();

    candles.forEach(c => {
        const t = c.timestamp;
        if (seenTimes.has(t)) return;
        seenTimes.add(t);

        cData.push({
            time: t,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close
        });

        if (c.ema18) ema18Data.push({ time: t, value: c.ema18 });
        if (c.ema50) ema50Data.push({ time: t, value: c.ema50 });
    });

    cData.sort((a, b) => a.time - b.time);
    ema18Data.sort((a, b) => a.time - b.time);
    ema50Data.sort((a, b) => a.time - b.time);

    candleSeries.setData(cData);
    if (ema18Series && ema18Data.length > 0) ema18Series.setData(ema18Data);
    if (ema50Series && ema50Data.length > 0) ema50Series.setData(ema50Data);

    if (chart) chart.timeScale().fitContent();
}

function renderPriceLines(data) {
    if (!candleSeries || !data || !data.risk_details) return;
    const rd = data.risk_details;

    if (poiPriceLine) {
        candleSeries.removePriceLine(poiPriceLine);
        poiPriceLine = null;
    }
    if (cutLossPriceLine) {
        candleSeries.removePriceLine(cutLossPriceLine);
        cutLossPriceLine = null;
    }

    if (rd.poi) {
        poiPriceLine = candleSeries.createPriceLine({
            price: rd.poi,
            color: '#38BDF8',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: 'POI',
        });
    }

    if (rd.invalidation) {
        cutLossPriceLine = candleSeries.createPriceLine({
            price: rd.invalidation,
            color: '#EF5350',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: 'Cut loss',
        });
    }
}

function renderEvaluation(data) {
    if (!data) return;

    const action = data.action || "HOLD";
    const score = data.confluence_score || 0;
    const vDir = document.getElementById("verdictDirection");
    const vScore = document.getElementById("verdictScore");

    let text = "Netral (Konsolidasi)";
    let cls = "neutral";

    if (action === "BUY") {
        text = "Bullish (Akumulasi)";
        cls = "bull";
    } else if (action === "SELL") {
        text = "Bearish (Distribusi)";
        cls = "bear";
    }

    if (vDir) {
        vDir.textContent = text;
        vDir.className = `verdict-signal ${cls}`;
    }
    if (vScore) vScore.textContent = `${score.toFixed(1)}%`;

    const poiEl = document.getElementById("valPoi");
    const invEl = document.getElementById("valInvalidation");
    const tp1El = document.getElementById("valTp1");
    const tp2El = document.getElementById("valTp2");

    if (data.risk_details) {
        const rd = data.risk_details;
        if (poiEl) poiEl.textContent = `Rp ${parseInt(rd.poi || 0).toLocaleString()}`;
        if (invEl) invEl.textContent = `Rp ${parseInt(rd.invalidation || 0).toLocaleString()} (-${rd.risk_pct || 0}%)`;
        if (tp1El) tp1El.textContent = `Rp ${parseInt(rd.tp1_rr2 || 0).toLocaleString()}`;
        if (tp2El) tp2El.textContent = `Rp ${parseInt(rd.tp2_rr3 || 0).toLocaleString()}`;
    }

    const sub = data.sub_scores || {};
    const p1 = sub.trend_score || 0;
    const p2 = sub.snd_score || 0;
    const p3 = sub.macro_score || 0;

    const sTrend = document.getElementById("scoreTrend");
    const sSnd = document.getElementById("scoreSnd");
    const sMacro = document.getElementById("scoreMacro");

    if (sTrend) sTrend.textContent = `${p1.toFixed(1)}%`;
    if (sSnd) sSnd.textContent = `${p2.toFixed(1)}%`;
    if (sMacro) sMacro.textContent = `${p3.toFixed(1)}%`;

    const bTrend = document.getElementById("barTrend");
    const bSnd = document.getElementById("barSnd");
    const bMacro = document.getElementById("barMacro");

    if (bTrend) bTrend.style.width = `${p1}%`;
    if (bSnd) bSnd.style.width = `${p2}%`;
    if (bMacro) bMacro.style.width = `${p3}%`;

    const dMem = document.getElementById("dossierMemory");
    const dTech = document.getElementById("dossierTech");
    const dMacro = document.getElementById("dossierMacro");
    const dConf = document.getElementById("dossierConfluence");
    const dRisk = document.getElementById("dossierRisk");

    if (dMem) dMem.textContent = data.memory_match || "-";
    if (dTech) dTech.textContent = data.technical_analysis || "-";
    if (dMacro) dMacro.textContent = data.fundamental_analysis || "-";
    if (dConf) dConf.textContent = `${score.toFixed(1)}% (${data.confluence_breakdown})`;
    if (dRisk) dRisk.textContent = data.poi_invalidation || "-";
}
