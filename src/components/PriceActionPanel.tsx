import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { Activity, ArrowUp, ArrowDown } from "lucide-react";
import { useState } from "react";

const generatePriceData = () => {
  const data = [];
  let price = 97500;
  for (let i = 0; i < 48; i++) {
    price += (Math.random() - 0.48) * 200;
    data.push({
      time: `${String(Math.floor(i / 2)).padStart(2, "0")}:${i % 2 === 0 ? "00" : "30"}`,
      price: Math.round(price * 100) / 100,
      volume: Math.floor(Math.random() * 500 + 100),
    });
  }
  return data;
};

const priceData = generatePriceData();

const timeframes = ["1M", "5M", "15M", "1H", "4H", "1D"];

export const PriceActionPanel = () => {
  const [activeTimeframe, setActiveTimeframe] = useState("1H");
  
  const firstPrice = priceData[0].price;
  const lastPrice = priceData[priceData.length - 1].price;
  const priceChange = lastPrice - firstPrice;
  const isPositive = priceChange >= 0;

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <span className="panel-title">BTC/USD PRICE ACTION</span>
          </div>
          
          <div className="flex items-center gap-1">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => setActiveTimeframe(tf)}
                className={`px-2 py-1 text-xs font-mono rounded transition-colors ${
                  activeTimeframe === tf
                    ? "bg-primary text-primary-foreground"
                    : "bg-panel-bg text-muted-foreground hover:bg-primary/20"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-2xl font-mono font-bold text-foreground">
              ${lastPrice.toLocaleString()}
            </div>
            <div
              className={`flex items-center gap-1 text-sm font-mono ${
                isPositive ? "text-terminal-green" : "text-danger-red"
              }`}
            >
              {isPositive ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
              {isPositive ? "+" : ""}
              {priceChange.toFixed(2)} ({((priceChange / firstPrice) * 100).toFixed(2)}%)
            </div>
          </div>
        </div>
      </div>

      <div className="h-48 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={priceData}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={isPositive ? "hsl(var(--terminal-green))" : "hsl(var(--danger-red))"}
                  stopOpacity={0.4}
                />
                <stop
                  offset="95%"
                  stopColor={isPositive ? "hsl(var(--terminal-green))" : "hsl(var(--danger-red))"}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
              interval={7}
            />
            <YAxis
              domain={["dataMin - 100", "dataMax + 100"]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
              width={50}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--panel-bg))",
                border: "1px solid hsl(var(--primary))",
                borderRadius: "4px",
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "12px",
              }}
              labelStyle={{ color: "hsl(var(--primary))" }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, "Price"]}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={isPositive ? "hsl(var(--terminal-green))" : "hsl(var(--danger-red))"}
              strokeWidth={2}
              fill="url(#priceGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 pt-2 border-t border-primary/20 grid grid-cols-4 gap-4 text-xs">
        <div>
          <span className="text-muted-foreground">HIGH</span>
          <div className="font-mono text-terminal-green">$98,234.50</div>
        </div>
        <div>
          <span className="text-muted-foreground">LOW</span>
          <div className="font-mono text-danger-red">$96,890.00</div>
        </div>
        <div>
          <span className="text-muted-foreground">OPEN</span>
          <div className="font-mono text-foreground">$97,125.00</div>
        </div>
        <div>
          <span className="text-muted-foreground">24H VOL</span>
          <div className="font-mono text-primary">2.4B USD</div>
        </div>
      </div>
    </div>
  );
};
