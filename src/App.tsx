import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Plan from "./pages/Plan";
import Action from "./pages/Action";
import Portfolio from "./pages/Portfolio";
import NotFound from "./pages/NotFound";

import { GlobalGamepadHandler } from "@/components/GlobalGamepadHandler";
import { SocketProvider } from "@/context/SocketContext";
import { AudioProvider } from "@/context/AudioContext";
import { useAudioKeyboard } from "@/hooks/useAudioKeyboard";

const queryClient = new QueryClient();

const AppContent = () => {
  // Register global audio keyboard shortcuts
  useAudioKeyboard();

  return (
    <BrowserRouter>
      <GlobalGamepadHandler />
      <Routes>
        <Route path="/plan" element={<Plan />} />
        <Route path="/action" element={<Action />} />
        <Route path="/" element={<Portfolio />} />
        {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AudioProvider>
      <SocketProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <AppContent />
        </TooltipProvider>
      </SocketProvider>
    </AudioProvider>
  </QueryClientProvider>
);

export default App;
