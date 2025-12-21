import { NavLink } from "react-router-dom";
import { Monitor, BarChart3, Settings, Radio } from "lucide-react";

const monitors = [
  { path: "/", label: "MON 1", title: "MARKET", icon: BarChart3 },
  { path: "/monitor-2", label: "MON 2", title: "TRADE OPS", icon: Settings },
  { path: "/monitor-3", label: "MON 3", title: "SYSTEM", icon: Radio },
];

export const MonitorNav = () => {
  return (
    <div className="flex items-center gap-1 bg-panel-bg/50 p-1 rounded border border-primary/20">
      <Monitor className="w-4 h-4 text-muted-foreground mx-2" />
      {monitors.map((mon) => (
        <NavLink
          key={mon.path}
          to={mon.path}
          className={({ isActive }) =>
            `flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded transition-all ${
              isActive
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-primary/20 hover:text-primary"
            }`
          }
        >
          <mon.icon className="w-3 h-3" />
          <span className="hidden sm:inline">{mon.label}:</span>
          <span>{mon.title}</span>
        </NavLink>
      ))}
    </div>
  );
};
