import { Clock, X, CheckCircle, AlertCircle } from "lucide-react";

const activeOrders = [
  {
    id: "ORD-4521",
    pair: "BTC/USD",
    type: "LIMIT BUY",
    price: "96,500.00",
    size: "0.15",
    filled: 0,
    status: "pending",
    time: "14:32:18",
  },
  {
    id: "ORD-4520",
    pair: "ETH/USD",
    type: "STOP LOSS",
    price: "3,380.00",
    size: "2.5",
    filled: 0,
    status: "active",
    time: "14:28:45",
  },
  {
    id: "ORD-4519",
    pair: "BTC/USD",
    type: "TAKE PROFIT",
    price: "99,000.00",
    size: "0.10",
    filled: 0,
    status: "active",
    time: "14:15:22",
  },
  {
    id: "ORD-4518",
    pair: "SOL/USD",
    type: "LIMIT BUY",
    price: "182.50",
    size: "25",
    filled: 60,
    status: "partial",
    time: "13:58:10",
  },
  {
    id: "ORD-4517",
    pair: "XAU/USD",
    type: "LIMIT SELL",
    price: "2,650.00",
    size: "5",
    filled: 100,
    status: "filled",
    time: "13:45:33",
  },
];

const getStatusIcon = (status: string) => {
  switch (status) {
    case "filled":
      return <CheckCircle className="w-4 h-4 text-terminal-green" />;
    case "partial":
      return <Clock className="w-4 h-4 text-primary animate-pulse" />;
    case "active":
      return <AlertCircle className="w-4 h-4 text-secondary" />;
    default:
      return <Clock className="w-4 h-4 text-muted-foreground" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case "filled":
      return "text-terminal-green";
    case "partial":
      return "text-primary";
    case "active":
      return "text-secondary";
    default:
      return "text-muted-foreground";
  }
};

export const ActiveOrdersPanel = () => {
  return (
    <div className="panel h-full">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-secondary" />
          <span className="panel-title">ACTIVE ORDERS</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-mono">
            {activeOrders.filter((o) => o.status !== "filled").length} PENDING
          </span>
          <div className="status-indicator online">
            <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
          </div>
        </div>
      </div>

      <div className="space-y-1">
        {/* Header */}
        <div className="grid grid-cols-8 gap-2 text-xs text-muted-foreground px-2 py-1 border-b border-primary/20">
          <span>ORDER ID</span>
          <span>PAIR</span>
          <span>TYPE</span>
          <span className="text-right">PRICE</span>
          <span className="text-right">SIZE</span>
          <span className="text-center">FILLED</span>
          <span className="text-center">STATUS</span>
          <span className="text-center">ACTION</span>
        </div>

        {/* Orders */}
        {activeOrders.map((order, index) => (
          <div
            key={order.id}
            className={`grid grid-cols-8 gap-2 text-sm px-2 py-2 font-mono transition-colors hover:bg-primary/10 ${
              index % 2 === 0 ? "bg-panel-bg/50" : "bg-background/50"
            } ${order.status === "filled" ? "opacity-60" : ""}`}
          >
            <span className="text-muted-foreground">{order.id}</span>
            <span className="text-primary font-bold">{order.pair}</span>
            <span
              className={
                order.type.includes("BUY")
                  ? "text-terminal-green"
                  : order.type.includes("SELL")
                  ? "text-danger-red"
                  : "text-secondary"
              }
            >
              {order.type}
            </span>
            <span className="text-right text-foreground">${order.price}</span>
            <span className="text-right text-foreground">{order.size}</span>
            <div className="flex justify-center">
              <div className="w-12 h-1.5 bg-background rounded-full overflow-hidden">
                <div
                  className="h-full bg-terminal-green rounded-full transition-all"
                  style={{ width: `${order.filled}%` }}
                />
              </div>
            </div>
            <div className="flex items-center justify-center gap-1">
              {getStatusIcon(order.status)}
              <span className={`text-xs ${getStatusColor(order.status)}`}>
                {order.status.toUpperCase()}
              </span>
            </div>
            <div className="flex justify-center">
              {order.status !== "filled" && (
                <button className="p-1 hover:bg-danger-red/20 rounded transition-colors group">
                  <X className="w-4 h-4 text-muted-foreground group-hover:text-danger-red" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-2 border-t border-primary/20 flex justify-between text-xs">
        <span className="text-muted-foreground">Total Orders: {activeOrders.length}</span>
        <span className="text-terminal-green">
          Filled: {activeOrders.filter((o) => o.status === "filled").length}
        </span>
      </div>
    </div>
  );
};
