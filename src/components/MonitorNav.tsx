import { NavLink } from "react-router-dom";
import { Monitor, BarChart3, Diamond, BriefcaseBusiness } from "lucide-react";

const monitors = [
  { path: "/", label: "1", title: "UPDATES", icon: BarChart3 },
  { path: "/m2", label: "2", title: "ACTIONS", icon: Diamond },
  { path: "/m3", label: "3", title: "PORTFOLIO", icon: BriefcaseBusiness },
];

export const MonitorNav = () => {
  return (
    <div className="flex items-center gap-1 bg-panel-bg/50 p-1 rounded border border-primary/20">
      {/* <Monitor className="w-4 h-4 text-muted-foreground mx-2" /> */}
      {monitors.map((mon) => (
        <NavLink
          key={mon.path}
          to={mon.path}
          className={({ isActive }) =>
            `flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded transition-all ${isActive
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
