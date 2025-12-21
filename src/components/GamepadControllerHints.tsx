import { Gamepad2 } from "lucide-react";

export const GamepadControllerHints = () => {
  return (
    <div className="panel bg-panel-bg/30">
      <div className="flex items-center justify-between flex-wrap gap-4 p-3">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Gamepad2 className="w-5 h-5 text-primary" />
          <span className="text-sm font-mono">CONTROLLER READY</span>
        </div>

        <div className="flex items-center gap-6 flex-wrap">
          {/* D-Pad */}
          <div className="flex items-center gap-2">
            <div className="flex flex-col items-center">
              <div className="w-5 h-5 border border-primary/50 rounded-sm flex items-center justify-center text-xs text-primary">▲</div>
              <div className="flex">
                <div className="w-5 h-5 border border-primary/50 rounded-sm flex items-center justify-center text-xs text-primary">◄</div>
                <div className="w-5 h-5" />
                <div className="w-5 h-5 border border-primary/50 rounded-sm flex items-center justify-center text-xs text-primary">►</div>
              </div>
              <div className="w-5 h-5 border border-primary/50 rounded-sm flex items-center justify-center text-xs text-primary">▼</div>
            </div>
            <span className="text-xs text-muted-foreground">NAVIGATE</span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint bg-terminal-green/20 text-terminal-green text-xs">A</div>
              <span className="text-xs text-muted-foreground">CONFIRM</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint bg-danger-red/20 text-danger-red text-xs">B</div>
              <span className="text-xs text-muted-foreground">BACK</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint bg-primary/20 text-primary text-xs">X</div>
              <span className="text-xs text-muted-foreground">ACTION</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint bg-secondary/20 text-secondary text-xs">Y</div>
              <span className="text-xs text-muted-foreground">SPECIAL</span>
            </div>
          </div>

          {/* Bumpers */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint text-xs px-2">LB</div>
              <span className="text-xs text-muted-foreground">TRADE</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint text-xs px-2">RB</div>
              <span className="text-xs text-muted-foreground">POSITIONS</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
