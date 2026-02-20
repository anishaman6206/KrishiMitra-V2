import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./lib/store";
import { ErrorBoundary } from "./components/ErrorBoundary";
import Shell, { TabBar } from "./Shell";
import Index from "./pages/Index";
import HomePage from "./pages/HomePage";
import CropsPage from "./pages/CropsPage";
import SoilPage from "./pages/SoilPage";
import MarketPage from "./pages/MarketPage";
import ProfilePage from "./pages/ProfilePage";
import DiseasePage from "./pages/DiseasePage";
import AskAIPage from "./pages/AskAIPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <ErrorBoundary>
    <AppProvider>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <div className="min-h-screen bg-background text-foreground flex flex-col">
              <div className="flex-1">
                <Shell>
                  <Routes>
                    <Route path="/" element={<Index />} />
                    <Route path="/home" element={<HomePage />} />
                    <Route path="/crops" element={<CropsPage />} />
                    <Route path="/soil" element={<SoilPage />} />
                    <Route path="/market" element={<MarketPage />} />
                    <Route path="/profile" element={<ProfilePage />} />
                    <Route path="/disease" element={<DiseasePage />} />
                    <Route path="/ask" element={<AskAIPage />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </Shell>
              </div>
              <TabBar />
            </div>
          </BrowserRouter>
        </TooltipProvider>
      </QueryClientProvider>
    </AppProvider>
  </ErrorBoundary>
);

export default App;
