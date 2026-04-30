import { useState, useEffect } from 'react';
import axios from 'axios';
import { AdvancedRealTimeChart } from 'react-ts-tradingview-widgets';
import './App.css';

interface Signal {
  id: number;
  action: string;
  symbol: string;
  exchange?: string;
  timeframe: string;
  price: number;
  timestamp: string;
  received_at: string;
}

function App() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [currentSignal, setCurrentSignal] = useState<Signal | null>(null);
  const [loading, setLoading] = useState(true); 
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const fetchSignals = async () => {
    try {
      const res = await axios.get('/signals?limit=50');
      setSignals(res.data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch signals:', err);
      setLoading(false);
    }
  };

function getColor(rsi: number) {
  if (rsi > 60) return "#00ff88";
  if (rsi >= 50) return "#ffa500";
  return "#ff4d4d";
}

function calcRSI(prices: number[], period = 14) {
  if (prices.length < period + 1) return 50;

  let gains = 0;
  let losses = 0;

  for (let i = prices.length - period; i < prices.length; i++) {
    const diff = prices[i] - prices[i - 1];
    if (diff >= 0) gains += diff;
    else losses -= diff;
  }

  const rs = gains / (losses || 1);
  return 100 - 100 / (1 + rs);
}
  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (signals.length > 0 && !currentSignal) {
      setCurrentSignal(signals[0]);
    }
  }, [signals]);

useEffect(() => {
  const canvas = canvasRef.current;
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  function draw() {
    if (!emaData.length) return;

    canvas.width = canvas.clientWidth;
    canvas.height = 220;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const prices = emaData.map(d => d.price);
    const max = Math.max(...prices);
    const min = Math.min(...prices);

    const scaleY = (v: number) =>
      canvas.height - ((v - min) / (max - min)) * canvas.height;

    const scaleX = (i: number) =>
      (i / (emaData.length - 1)) * canvas.width;

    function drawSeries(
      emaKey: "ema15" | "ema1h" | "ema3h",
      rsiKey: "rsi15" | "rsi1h" | "rsi3h"
    ) {
      for (let i = 1; i < emaData.length; i++) {
        const prev = emaData[i - 1];
        const curr = emaData[i];

        ctx.beginPath();
        ctx.strokeStyle = getColor(curr[rsiKey]);
        ctx.lineWidth = 2;

        ctx.moveTo(scaleX(i - 1), scaleY(prev[emaKey]));
        ctx.lineTo(scaleX(i), scaleY(curr[emaKey]));

        ctx.stroke();
      }
    }

    drawSeries("ema15", "rsi15");
    drawSeries("ema1h", "rsi1h");
    drawSeries("ema3h", "rsi3h");
  }

  draw();
}, [emaData]);

  const loadChart = (signal: Signal) => {
    setCurrentSignal(signal);
  };

  const tvSymbol = currentSignal 
    ? `${currentSignal.exchange || 'NASDAQ'}:${currentSignal.symbol}` 
    : 'NASDAQ:AAPL';

  const getValidInterval = (tf: string | undefined): string => {
    if (!tf) return "15";
    const timeframe = tf.toUpperCase().trim();
    
    if (["1", "1M", "1MIN"].includes(timeframe)) return "1";
    if (["3", "3M", "3MIN"].includes(timeframe)) return "3";
    if (["5", "5M", "5MIN"].includes(timeframe)) return "5";
    if (["15", "15M", "15MIN"].includes(timeframe)) return "15";
    if (["30", "30M", "30MIN"].includes(timeframe)) return "30";
    if (["60", "1H", "60MIN"].includes(timeframe)) return "60";
    if (["120", "2H"].includes(timeframe)) return "120";
    if (["180", "3H"].includes(timeframe)) return "180";
    if (["240", "4H"].includes(timeframe)) return "240";
    if (["D", "1D", "DAY"].includes(timeframe)) return "D";
    if (["W", "1W", "WEEK"].includes(timeframe)) return "W";
    
    return "15";
  };

 const tvInterval = getValidInterval(currentSignal?.timeframe);

<div className="box">
  <h3>📊 EMA + RSI Canvas Chart</h3>

  <canvas
    ref={canvasRef}
    style={{
      width: "100%",
      height: "220px",
      background: "#111",
      borderRadius: "8px"
    }}
  />
</div>

  return (
    <div className="app">
      <header className="header">
        <h1>📈 Stock Trade Scanner</h1>
        <p>Live signals from TradingView • Click any row to view chart</p>
      </header>

      <div className="dashboard">
        <div className="scanner-panel">
          <div className="panel-header">
            <h2>Live Signals</h2>
            <button onClick={fetchSignals} className="refresh-btn">Refresh</button>
          </div>

          {loading ? (
            <p>Loading signals...</p>
          ) : signals.length === 0 ? (
            <p>No signals yet. Waiting for TradingView alerts...</p>
          ) : (
            <table className="signals-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Symbol</th>
                  <th>Timeframe</th>
                  <th>Price</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((sig) => (
                  <tr 
                    key={sig.id} 
                    onClick={() => loadChart(sig)}
                    className={currentSignal?.id === sig.id ? 'selected' : ''}
                  >
                    <td className={`action ${sig.action.toLowerCase()}`}>
                      {sig.action}
                    </td>
                    <td className="symbol">{sig.symbol}</td>
                    <td>{sig.timeframe}</td>
                    <td className="price">${sig.price.toFixed(2)}</td>
                    <td className="time">
                      {new Date(sig.received_at).toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="chart-panel">
          <div className="panel-header">
            <h2>
              {currentSignal 
                ? `${currentSignal.action} ${tvSymbol} (${tvInterval})` 
                : 'Select a signal from the table'}
            </h2>
          </div>
          <div className="chart-container">
            <AdvancedRealTimeChart
              symbol={tvSymbol}
              interval={tvInterval as "1" | "3" | "5" | "15" | "30" | "60" | "120" | "180" | "240" | "D" | "W"}
              theme="dark"
              autosize={true}
              allow_symbol_change={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;