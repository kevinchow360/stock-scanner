import React, { useEffect, useRef, useState } from "react";

export default function TradingDashboard() {
  const containerRef = useRef(null);
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [latestSignal, setLatestSignal] = useState(null);

  useEffect(() => {
    // ---------------- WebSocket ----------------
    const socket = new WebSocket("ws://localhost:8000/ws");
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      console.log("WebSocket connected");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLatestSignal(data);
      } catch (err) {
        console.error("Invalid message", err);
      }
    };

    socket.onclose = () => {
      setConnected(false);
      console.log("WebSocket disconnected");
    };

    return () => socket.close();
  }, []);

  useEffect(() => {
    // ---------------- TradingView Widget ----------------
    if (!containerRef.current) return;

    containerRef.current.innerHTML = "";

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = () => {
      if (window.TradingView) {
        new window.TradingView.widget({
          width: "100%",
          height: 600,
          symbol: "NASDAQ:AAPL",
          interval: "1",
          timezone: "Etc/UTC",
          theme: "dark",
          style: "1",
          locale: "en",
          toolbar_bg: "#1e1e1e",
          enable_publishing: false,
          hide_top_toolbar: false,
          hide_legend: false,
          save_image: false,
          container_id: containerRef.current,
        });
      }
    };

    document.body.appendChild(script);
  }, []);

  return (
    <div style={{ padding: 20, fontFamily: "Arial" }}>
      <h1>📊 Live Trading Dashboard</h1>

      <div style={{ marginBottom: 10 }}>
        Status: {connected ? "🟢 Live" : "🔴 Disconnected"}
      </div>

      {latestSignal && (
        <div style={{ padding: 10, background: "#111", color: "#0f0", marginBottom: 20 }}>
          <div>Latest Signal</div>
          <div>
            {latestSignal.action} {latestSignal.symbol} @ {latestSignal.price}
          </div>
        </div>
      )}

      {/* TradingView Chart */}
      <div ref={containerRef} />
    </div>
  );
}
