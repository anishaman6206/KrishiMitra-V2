import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../lib/store";
import { ai } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Mic, Camera, Edit, ArrowLeft, Sun, DollarSign, Droplets, Leaf } from "lucide-react";
import { toast } from "sonner";

export default function AskAIPage() {
  const navigate = useNavigate();
  const { state } = useApp();
  const [question, setQuestion] = useState("");
  const [language, setLanguage] = useState(state.user?.language_pref || "en");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const farmId = state.farm?.id || undefined;
  const district = state.farm?.district || undefined;

  async function ask() {
    if (!question.trim()) {
      toast.error("Please enter a question");
      return;
    }

    setLoading(true);
    setAnswer(null);
    
    try {
      const coords =
        state.farm?.latitude != null && state.farm?.longitude != null
          ? { lat: state.farm.latitude, lon: state.farm.longitude }
          : undefined;

      const res = await ai.askAgentic({
        question,
        target_language: language,
        coords,
        market: { district },
        farmId,
      });
      
      setAnswer(res.answer);
    } catch (e: any) {
      toast.error(e?.message || "Failed to get answer");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/home")}
          className="rounded-full"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Ask AI</h1>
          <p className="text-sm text-muted-foreground">Voice, text, or photo queries</p>
        </div>
      </div>

      {/* Voice Interface Card */}
      <Card className="border-2 border-primary/20">
        <CardContent className="p-8 text-center">
          <Button 
            className="w-40 h-40 rounded-full bg-primary hover:bg-primary/90 border-4 border-primary/30 shadow-2xl mb-6"
            onClick={() => toast.info("Voice feature coming soon!")}
          >
            <Mic className="w-20 h-20 text-primary-foreground" />
          </Button>
          
          {/* Animated sound waves */}
          <div className="flex justify-center space-x-1 mb-4">
            <div className="w-1 h-8 bg-primary/30 rounded-full animate-pulse"></div>
            <div className="w-1 h-12 bg-primary/50 rounded-full animate-pulse delay-75"></div>
            <div className="w-1 h-6 bg-primary/40 rounded-full animate-pulse delay-150"></div>
            <div className="w-1 h-10 bg-primary/60 rounded-full animate-pulse delay-300"></div>
            <div className="w-1 h-4 bg-primary/20 rounded-full animate-pulse delay-500"></div>
          </div>
          
          <h2 className="text-lg font-semibold mb-2">Tap to Speak</h2>
          <p className="text-muted-foreground">Ask questions in your language</p>
        </CardContent>
      </Card>

      {/* Query Options */}
      <div className="grid grid-cols-3 gap-4">
        <Button variant="outline" className="h-16 flex flex-col items-center justify-center gap-2 rounded-xl border-2">
          <Mic className="w-6 h-6 text-primary" />
          <span className="text-xs font-medium">Voice</span>
        </Button>
        <Button variant="outline" className="h-16 flex flex-col items-center justify-center gap-2 rounded-xl border-2 bg-primary/5 border-primary">
          <Edit className="w-6 h-6 text-primary" />
          <span className="text-xs font-medium">Text</span>
        </Button>
        <Button variant="outline" className="h-16 flex flex-col items-center justify-center gap-2 rounded-xl border-2">
          <Camera className="w-6 h-6 text-green-500" />
          <span className="text-xs font-medium">Photo</span>
        </Button>
      </div>

      {/* Text Query Card */}
      <Card>
        <CardHeader>
          <CardTitle>Ask in Text</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Textarea 
              placeholder="Ask about market prices, weather, soil, best time to sell, or farming advice..."
              className="min-h-[100px]"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>
          
          <div className="flex gap-3">
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="hi">हिंदी</SelectItem>
                <SelectItem value="bn">বাংলা</SelectItem>
                <SelectItem value="te">తెలుగు</SelectItem>
                <SelectItem value="mr">मराठी</SelectItem>
                <SelectItem value="ta">தமிழ்</SelectItem>
              </SelectContent>
            </Select>
            
            <Button 
              onClick={ask} 
              disabled={loading || !question.trim()}
              className="flex-1"
            >
              {loading ? "Thinking..." : "Ask AI Assistant"}
            </Button>
          </div>

          {answer && (
            <div className="mt-4 p-4 bg-muted rounded-lg whitespace-pre-wrap">
              {answer}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Commands */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>⚡</span>
            Quick Commands
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <Button 
              variant="outline" 
              className="h-14 flex flex-col items-center justify-center gap-1 rounded-xl"
              onClick={() => {
                setQuestion("What's the weather forecast for the next week?");
              }}
            >
              <Sun className="w-5 h-5 text-yellow-500" />
              <span className="text-sm font-medium">Weather Update</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-14 flex flex-col items-center justify-center gap-1 rounded-xl"
              onClick={() => {
                setQuestion("What are the current market prices for my crops?");
              }}
            >
              <DollarSign className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium">Market Prices</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-14 flex flex-col items-center justify-center gap-1 rounded-xl"
              onClick={() => {
                setQuestion("Give me a soil health report for my farm");
              }}
            >
              <Droplets className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium">Soil Report</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-14 flex flex-col items-center justify-center gap-1 rounded-xl"
              onClick={() => {
                setQuestion("Which crops should I plant this season?");
              }}
            >
              <Leaf className="w-5 h-5 text-primary" />
              <span className="text-sm font-medium">Crop Advice</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
