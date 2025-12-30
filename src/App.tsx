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

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <SocketProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
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
      </TooltipProvider>
    </SocketProvider>
  </QueryClientProvider>
);

export default App;
