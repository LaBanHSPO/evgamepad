import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Volume2, VolumeX, MessageCircle, Sparkles, Play, User } from "lucide-react";

interface Message {
  id: number;
  text: string;
  isAI: boolean;
  timestamp: string;
  isNew?: boolean;
}

const initialMessages: Message[] = [
  {
    id: 1,
    text: "Good morning, Trader! I've been analyzing the markets while you were away. BTC is showing strong bullish momentum on the H4 timeframe.",
    isAI: true,
    timestamp: "08:30",
  },
  {
    id: 2,
    text: "I found a solid support level at $96,500. The risk/reward ratio looks favorable at 1:2.8. Want me to break it down for you?",
    isAI: true,
    timestamp: "08:31",
  },
];

const aiResponses = [
  "I'm seeing increased whale activity on-chain. This often precedes significant moves. Stay alert!",
  "The Fear & Greed index just shifted to 'Greed'. Historically, this suggests we might see some volatility ahead.",
  "Your current position is looking good! The trend is still intact. I'd recommend holding for now.",
  "I've spotted a potential divergence forming on the RSI. Let me keep monitoring this for you.",
  "Great news! The support level I mentioned earlier is holding strong. Confidence in this trade remains high.",
  "Remember to take breaks, Trader. A clear mind makes better decisions. I'll watch the charts for you.",
];

const CapitalCompanionPanel = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isTalking, setIsTalking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const [aiMood, setAiMood] = useState<"happy" | "thinking" | "alert">("happy");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Simulate incoming AI messages periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const randomChance = Math.random();
      if (randomChance > 0.7) {
        setAiMood("thinking");
        setIsThinking(true);

        setTimeout(() => {
          const randomResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];
          const newMessage: Message = {
            id: Date.now(),
            text: randomResponse,
            isAI: true,
            timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
            isNew: true,
          };
          setMessages(prev => [...prev, newMessage]);
          setHasNewMessage(true);
          setIsThinking(false);
          setAiMood("happy");

          // Remove "new" indicator after a few seconds
          setTimeout(() => {
            setMessages(prev => prev.map(m => m.id === newMessage.id ? { ...m, isNew: false } : m));
            setHasNewMessage(false);
          }, 3000);
        }, 2000);
      }
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const handleTalkToggle = () => {
    setIsTalking(!isTalking);
    if (!isTalking) {
      // Simulate user talking
      setTimeout(() => {
        setIsTalking(false);
        setAiMood("thinking");
        setIsThinking(true);

        // AI responds
        setTimeout(() => {
          const responses = [
            "I understand your concern. Let me analyze that for you...",
            "That's a great question! Based on my analysis...",
            "I'm on it, Trader! Give me a moment to crunch the numbers.",
          ];
          const newMessage: Message = {
            id: Date.now(),
            text: responses[Math.floor(Math.random() * responses.length)],
            isAI: true,
            timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
            isNew: true,
          };
          setMessages(prev => [...prev, newMessage]);
          setIsThinking(false);
          setAiMood("happy");
        }, 1500);
      }, 3000);
    }
  };

  const playLatestMessage = () => {
    setHasNewMessage(false);
    // Simulate playing audio
  };

  // Gamepad/Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // p = Play Message (Start)
      // m = Toggle Mute (Back)
      // v = Toggle Talk (L3)
      if (e.key === "p" && hasNewMessage) {
        playLatestMessage();
      } else if (e.key === "m") {
        setIsMuted(prev => !prev);
      } else if (e.key === "v") {
        handleTalkToggle();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [hasNewMessage, isTalking]); // Added isTalking to dependencies as handleTalkToggle uses it via closure/state

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-secondary" />
          <h2 className="panel-title">CAPITAL COMPANION</h2>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isThinking ? "bg-secondary animate-pulse" : "bg-terminal-green"}`} />
          <span className="text-xs text-terminal-green">AI FRIEND</span>
        </div>
      </div>

      <div className="p-4 flex gap-4">
        {/* AI Avatar Section */}
        <div className="flex flex-col items-center gap-3">
          {/* Avatar Container */}
          <div className={`relative w-24 h-24 rounded-full bg-gradient-to-br from-secondary/30 to-primary/30 border-2 
            ${isTalking ? "border-terminal-green animate-pulse" : isThinking ? "border-secondary" : "border-primary/50"}
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

          {/* AI Name */}
          <div className="text-center">
            <span className="text-sm font-bold text-primary">ATLAS</span>
            <span className="block text-xs text-muted-foreground">Your Trading AI</span>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2 w-full">
            {/* Talk Button */}
            <button
              onClick={handleTalkToggle}
              className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-all duration-300
                ${isTalking
                  ? "bg-terminal-green/20 border-terminal-green text-terminal-green animate-pulse"
                  : "bg-panel-bg border-primary/30 text-primary hover:border-primary hover:bg-primary/10"
                }`}
            >
              {isTalking ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              <span className="text-sm font-semibold">{isTalking ? "STOP" : "TALK"}</span>
            </button>

            {/* Play New Message Button */}
            <button
              onClick={playLatestMessage}
              disabled={!hasNewMessage}
              className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg border transition-all duration-300
                ${hasNewMessage
                  ? "bg-secondary/20 border-secondary text-secondary animate-pulse"
                  : "bg-panel-bg/30 border-border/30 text-muted-foreground opacity-50 cursor-not-allowed"
                }`}
            >
              <Play className="w-4 h-4" />
              <span className="text-xs">{hasNewMessage ? "NEW MSG" : "NO MSG"}</span>
            </button>

            {/* Mute Toggle */}
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg border transition-all
                ${isMuted
                  ? "bg-danger-red/20 border-danger-red/50 text-danger-red"
                  : "bg-panel-bg/30 border-border/30 text-muted-foreground hover:text-foreground"
                }`}
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              <span className="text-xs">{isMuted ? "MUTED" : "SOUND"}</span>
            </button>
          </div>
        </div>

        {/* Chat Messages Section */}
        <div className="flex-1 flex flex-col">
          <div className="flex items-center gap-2 mb-2">
            <MessageCircle className="w-4 h-4 text-primary" />
            <span className="text-xs text-muted-foreground">CONVERSATION</span>
          </div>

          <div className="flex-1 bg-background/30 border border-border/30 rounded-lg p-3 overflow-y-auto max-h-[200px] space-y-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-2 ${message.isNew ? "animate-pulse" : ""}`}
              >
                {/* Avatar */}
                <div className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs
                  ${message.isAI
                    ? "bg-gradient-to-br from-secondary/50 to-primary/50 border border-primary/30"
                    : "bg-terminal-green/20 border border-terminal-green/30"
                  }`}
                >
                  {message.isAI ? "A" : <User className="w-3 h-3" />}
                </div>

                {/* Message */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={`text-xs font-semibold ${message.isAI ? "text-primary" : "text-terminal-green"}`}>
                      {message.isAI ? "Atlas" : "You"}
                    </span>
                    <span className="text-xs text-muted-foreground">{message.timestamp}</span>
                    {message.isNew && (
                      <span className="text-xs bg-secondary/30 text-secondary px-1.5 py-0.5 rounded">NEW</span>
                    )}
                  </div>
                  <p className={`text-sm leading-relaxed ${message.isAI ? "text-foreground/90" : "text-foreground/70"}`}>
                    {message.text}
                  </p>
                </div>
              </div>
            ))}

            {/* Thinking indicator in chat */}
            {isThinking && (
              <div className="flex gap-2">
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-secondary/50 to-primary/50 border border-primary/30 flex items-center justify-center text-xs">
                  A
                </div>
                <div className="flex items-center gap-1 text-muted-foreground">
                  <span className="text-xs">Atlas is thinking</span>
                  <div className="flex gap-0.5">
                    <div className="w-1 h-1 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-1 h-1 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-1 h-1 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Status */}
          <div className="mt-2 flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              {isTalking ? "🎤 Listening..." : isThinking ? "🤔 Analyzing..." : "💚 Ready to help"}
            </span>
            <span className="text-primary">{messages.length} messages</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CapitalCompanionPanel;
