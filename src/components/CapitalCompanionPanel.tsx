import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Volume2, VolumeX, MessageCircle, Sparkles, Play, User, Send, Pin, LayoutTemplate, Target, ShieldCheck } from "lucide-react";
import { useSocket } from "@/context/SocketContext";
import { TechnicalAnalysisCard, TechnicalAnalysisData } from "./chat/TechnicalAnalysisCard";
import { PatternAnalysisCard, PatternAnalysisData } from "./chat/PatternAnalysisCard";
import { RiskAnalysisCard, RiskAnalysisData } from "./chat/RiskAnalysisCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";

interface Message {
  id: number;
  type: "text" | "technical" | "pattern" | "risk" | "error";
  text?: string;
  data?: any;
  isAI: boolean;
  timestamp: string;
  isNew?: boolean;
}

const CapitalCompanionPanel = () => {
  const { socket, isConnected } = useSocket();
  const [messages, setMessages] = useState<Message[]>([]);
  const [pinnedMessages, setPinnedMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTalking, setIsTalking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [aiMood, setAiMood] = useState<"happy" | "thinking" | "alert">("happy");
  const [view, setView] = useState<'chat' | 'pinned'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (view === 'chat') {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, view]);

  useEffect(() => {
    if (!socket) return;

    const handleTechnicalResult = (data: TechnicalAnalysisData) => {
      addMessage({ type: 'technical', data, isAI: true, text: `Technical analysis for ${data.symbol}` });
      setIsThinking(false);
    };

    const handlePatternResult = (data: PatternAnalysisData) => {
      addMessage({ type: 'pattern', data, isAI: true, text: `Pattern scan results for ${data.symbol}` });
      setIsThinking(false);
    };

    const handleRiskResult = (data: RiskAnalysisData) => {
      addMessage({ type: 'risk', data, isAI: true, text: `Risk analysis for ${data.symbol}` });
      setIsThinking(false);
    };

    const handleError = (error: { message: string, code?: string }) => {
      addMessage({ type: 'error', text: error.message || "An error occurred", isAI: true });
      setIsThinking(false);
      toast.error(`Advisor Error: ${error.message}`);
    };

    socket.on('advisor:technical_result', handleTechnicalResult);
    socket.on('advisor:pattern_result', handlePatternResult);
    socket.on('advisor:risk_result', handleRiskResult);
    socket.on('advisor:error', handleError);

    return () => {
      socket.off('advisor:technical_result', handleTechnicalResult);
      socket.off('advisor:pattern_result', handlePatternResult);
      socket.off('advisor:risk_result', handleRiskResult);
      socket.off('advisor:error', handleError);
    };
  }, [socket]);

  const addMessage = (msg: Omit<Message, "id" | "timestamp">) => {
    const newMessage: Message = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
      isNew: true,
      ...msg
    };
    setMessages(prev => [...prev, newMessage]);

    // Clear "new" status after 3s
    setTimeout(() => {
      setMessages(prev => prev.map(m => m.id === newMessage.id ? { ...m, isNew: false } : m));
    }, 3000);
  };

  const handleSendMessage = () => {
    if (!inputValue.trim() || !socket) return;

    // Check for commands
    const text = inputValue.trim();
    addMessage({ type: 'text', text, isAI: false });

    // Simple parsing for manual commands (fallback if not using templates)
    // E.g., "analyze XAUUSD"
    const parts = text.split(' ');
    const command = parts[0].toLowerCase();
    const symbol = parts[1]?.toUpperCase();

    if (symbol) {
      setIsThinking(true);
      if (command === 'analyze' || command === 'tech') {
        socket.emit('advisor:technical_summary', { symbol, timeframe: 'H1' });
      } else if (command === 'pattern' || command === 'scan') {
        socket.emit('advisor:pattern_scan', { symbol, timeframe: 'H1' });
      } else if (command === 'risk') {
        // Mock risk params for demo
        socket.emit('advisor:risk_analysis', {
          symbol,
          account_balance: 10000,
          entry_price: 2000, // Placeholder, would need real price
          stop_loss: 1990,
          take_profit: 2020
        });
      }
    }

    setInputValue("");
  };

  const handleTemplateClick = (type: string) => {
    if (!socket || !isConnected) {
      toast.error("Socket not connected");
      return;
    }
    // For demo, we might need a dialog to get Symbol. 
    // For now, let's just use a hardcoded symbol or prompt via simple alerts/fallback
    // A better UX would be selecting a symbol from the Market Overview first.
    // Let's assume user types symbol in input then clicks template, or we default to XAUUSD for demo.
    const symbol = inputValue.trim().toUpperCase() || "XAUUSD";

    setIsThinking(true);
    if (type === 'technical') {
      addMessage({ type: 'text', text: `Requesting Technical Analysis for ${symbol}...`, isAI: false });
      socket.emit('advisor:technical_summary', { symbol, timeframe: 'H1' });
    } else if (type === 'pattern') {
      addMessage({ type: 'text', text: `Scanning Patterns for ${symbol}...`, isAI: false });
      socket.emit('advisor:pattern_scan', { symbol, timeframe: 'H1' });
    } else if (type === 'risk') {
      addMessage({ type: 'text', text: `Calculating Risk for ${symbol}...`, isAI: false });
      // Using dummy values for quick action - in real app would open a form
      socket.emit('advisor:risk_analysis', {
        symbol,
        account_balance: 10000,
        entry_price: 2150,
        stop_loss: 2140,
        take_profit: 2170
      });
    }
  };

  const handlePinMessage = (message: Message) => {
    if (pinnedMessages.find(m => m.id === message.id)) return;
    setPinnedMessages(prev => [...prev, message]);
    toast.success("Insight pinned to dashboard");
  };

  const handleUnpinMessage = (id: number) => {
    setPinnedMessages(prev => prev.filter(m => m.id !== id));
  };

  const handleTalkToggle = () => {
    setIsTalking(!isTalking);
    if (!isTalking) {
      toast.info("Voice input not yet implemented");
      setTimeout(() => setIsTalking(false), 1000);
    }
  };

  const renderMessageContent = (message: Message, pinned = false) => {
    switch (message.type) {
      case 'technical':
        return <TechnicalAnalysisCard data={message.data} onPin={() => !pinned && handlePinMessage(message)} />;
      case 'pattern':
        return <PatternAnalysisCard data={message.data} onPin={() => !pinned && handlePinMessage(message)} />;
      case 'risk':
        return <RiskAnalysisCard data={message.data} onPin={() => !pinned && handlePinMessage(message)} />;
      case 'error':
        return <div className="text-danger-red p-2 bg-danger-red/10 rounded border border-danger-red/20">{message.text}</div>;
      default:
        return <p className={`text-sm leading-relaxed ${message.isAI ? "text-foreground/90" : "text-foreground/70"}`}>{message.text}</p>;
    }
  };

  return (
    <div className="panel h-[600px] flex flex-col">
      <div className="panel-header flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-secondary" />
          <h2 className="panel-title">CAPITAL COMPANION</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-terminal-green" : "bg-danger-red"}`} />
            <span className="text-[10px] text-muted-foreground">{isConnected ? "ONLINE" : "OFFLINE"}</span>
          </div>
          <button onClick={() => setView('chat')} className={`text-xs ${view === 'chat' ? 'text-primary font-bold' : 'text-muted-foreground'}`}>CHAT</button>
          <button onClick={() => setView('pinned')} className={`text-xs flex items-center gap-1 ${view === 'pinned' ? 'text-primary font-bold' : 'text-muted-foreground'}`}>
            <Pin className="w-3 h-3" /> PINNED ({pinnedMessages.length})
          </button>
        </div>
      </div>

      <div className="p-4 flex gap-4 flex-1 min-h-0">
        {/* Left Sidebar: Avatar & Quick Actions */}
        <div className="flex flex-col items-center gap-3 w-28 shrink-0">
          {/* Avatar Container */}
          <div className={`relative w-24 h-24 rounded-full bg-gradient-to-br from-secondary/30 to-primary/30 border-2 
            ${isTalking ? "border-terminal-green animate-pulse" : isThinking ? "border-secondary animate-pulse" : "border-primary/50"}
            flex items-center justify-center overflow-hidden transition-all duration-300`}
          >
            {/* AI Face */}
            <div className="relative">
              {/* Eyes */}
              <div className="flex gap-3 mb-2">
                <div className={`w-3 h-3 rounded-full bg-primary ${isThinking ? "animate-bounce" : ""}`}>
                  <div className="w-1 h-1 bg-white/80 rounded-full ml-0.5 mt-0.5" />
                </div>
                <div className={`w-3 h-3 rounded-full bg-primary ${isThinking ? "animate-bounce delay-100" : ""}`}>
                  <div className="w-1 h-1 bg-white/80 rounded-full ml-0.5 mt-0.5" />
                </div>
              </div>
              {/* Mouth */}
              <div className={`mx-auto w-6 h-2 rounded-full transition-all duration-300 
                ${aiMood === "happy" ? "bg-terminal-green" : aiMood === "thinking" ? "bg-secondary w-4 h-4" : "bg-danger-red"}`}
              />
            </div>

            {/* Glow effect when talking */}
            {isTalking && (
              <div className="absolute inset-0 bg-terminal-green/20 animate-pulse rounded-full" />
            )}

            {/* Thinking indicator */}
            {isThinking && (
              <div className="absolute -bottom-1 left-1/2 -translate-x-1/2">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}
          </div>

          <div className="text-center">
            <span className="text-sm font-bold text-primary">ATLAS</span>
            <span className="block text-[10px] text-muted-foreground">AI Advisor</span>
          </div>

          <div className="w-full space-y-1.5">
            <Button variant="outline" size="sm" className="w-full text-[10px] h-7 justify-start px-2 bg-background/50" onClick={() => handleTemplateClick('technical')}>
              <LayoutTemplate className="w-3 h-3 mr-1.5" /> Tech Summary
            </Button>
            <Button variant="outline" size="sm" className="w-full text-[10px] h-7 justify-start px-2 bg-background/50" onClick={() => handleTemplateClick('pattern')}>
              <Target className="w-3 h-3 mr-1.5" /> Pattern Scan
            </Button>
            <Button variant="outline" size="sm" className="w-full text-[10px] h-7 justify-start px-2 bg-background/50" onClick={() => handleTemplateClick('risk')}>
              <ShieldCheck className="w-3 h-3 mr-1.5" /> Risk Calc
            </Button>
          </div>

          <div className="mt-auto w-full flex justify-center">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMuted(!isMuted)}
              className={isMuted ? "text-danger-red" : "text-muted-foreground"}
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {view === 'chat' ? (
            <>
              <ScrollArea className="flex-1 pr-3 -mr-3">
                <div className="space-y-4 pb-2">
                  {messages.length === 0 && (
                    <div className="text-center text-muted-foreground text-xs py-10 opacity-50">
                      Start a conversation or select a template...
                    </div>
                  )}
                  {messages.map((message) => (
                    <div key={message.id} className={`flex gap-3 ${!message.isAI ? "flex-row-reverse" : ""}`}>
                      <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs
                            ${message.isAI ? "bg-gradient-to-br from-secondary/20 to-primary/20 border border-primary/30" : "bg-terminal-green/20 border border-terminal-green/30"}`}>
                        {message.isAI ? "A" : <User className="w-4 h-4" />}
                      </div>
                      <div className={`max-w-[85%] ${!message.isAI ? "items-end flex flex-col" : ""}`}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[10px] font-bold text-primary">{message.isAI ? "ATLAS" : "YOU"}</span>
                          <span className="text-[10px] text-muted-foreground">{message.timestamp}</span>
                        </div>
                        <div>{renderMessageContent(message)}</div>
                      </div>
                    </div>
                  ))}
                  {isThinking && (
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-full bg-secondary/10 border border-secondary/30 flex items-center justify-center text-xs">A</div>
                      <div className="flex items-center gap-1 text-muted-foreground text-xs h-8">
                        <span>Atlas is thinking</span>
                        <span className="animate-bounce">.</span><span className="animate-bounce delay-100">.</span><span className="animate-bounce delay-200">.</span>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              <div className="mt-3 flex gap-2">
                <Input
                  placeholder="Type symbol (e.g., BTCUSD) or command..."
                  className="bg-background/50 border-border/50 h-9 font-mono text-xs"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <Button size="icon" className="h-9 w-9 shrink-0" onClick={handleSendMessage}>
                  <Send className="w-4 h-4" />
                </Button>
                <Button
                  size="icon"
                  variant={isTalking ? "default" : "outline"}
                  className={`h-9 w-9 shrink-0 ${isTalking ? "bg-terminal-green text-black hover:bg-terminal-green/90" : ""}`}
                  onClick={handleTalkToggle}
                >
                  {isTalking ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
              </div>
            </>
          ) : (
            <ScrollArea className="flex-1">
              <div className="space-y-4">
                {pinnedMessages.length === 0 && <div className="text-center text-muted-foreground text-xs py-10">No pinned insights yet.</div>}
                {pinnedMessages.map((message) => (
                  <div key={message.id} className="relative group">
                    {renderMessageContent(message, true)}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 h-6 w-6 bg-background/80"
                      onClick={() => handleUnpinMessage(message.id)}
                    >
                      <Pin className="w-3 h-3 fill-current text-primary" />
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </div>
      </div>
    </div >
  );
};

export default CapitalCompanionPanel;
