import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../lib/store";
import { weather, soil, recos, geocodeFromPlace, type WeatherResponse, type SoilResponse, type CropReco } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Mic, Sun, Camera, DollarSign, MapPin, Wifi, Leaf, Cloud } from "lucide-react";

const STALE_MS = 30 * 60 * 1000; // 30 minutes

export default function HomePage() {
  const navigate = useNavigate();
  const { state, dispatch } = useApp();
  const [wx, setWx] = useState<WeatherResponse | null>(state.weatherCache.data);
  const [rc, setRc] = useState<CropReco[] | null>(state.recoCache.data);

  useEffect(() => {
    (async () => {
      if (!state.user || !state.farm) return;

      let coords = state.farm.latitude && state.farm.longitude
        ? { lat: state.farm.latitude, lon: state.farm.longitude }
        : null;
      
      if (!coords && state.farm.district) {
        const place = `${state.farm.district}${state.farm.state ? ", " + state.farm.state : ""}`;
        coords = await geocodeFromPlace(place).catch(() => null);
      }
      
      if (!coords) return;

      const key = `${coords.lat.toFixed(4)},${coords.lon.toFixed(4)}`;

      // WEATHER
      const wxFresh = state.weatherCache.key === key && state.weatherCache.ts && (Date.now() - state.weatherCache.ts) < STALE_MS;
      if (!wxFresh) {
        try {
          const w = await weather.get(coords);
          dispatch({ type: "SET_WEATHER", payload: { key, data: w } });
          setWx(w);
        } catch (e: any) {
          console.error("Weather error:", e);
        }
      }

      // RECO
      const rcFresh = state.recoCache.key === key && state.recoCache.ts && (Date.now() - state.recoCache.ts) < STALE_MS;
      if (!rcFresh) {
        try {
          const list = await recos.crops({ userId: state.user.id, coords });
          dispatch({ type: "SET_RECO", payload: { key, data: list } });
          setRc(list);
        } catch (e: any) {
          console.error("Reco error:", e);
        }
      }
    })();
  }, [state.user, state.farm, dispatch]);

  const greet = () => {
    const h = new Date().getHours();
    return h < 12 ? "Morning" : h < 18 ? "Afternoon" : "Evening";
  };

  return (
    <div className="space-y-6 pb-20">
      {/* Header Card */}
      <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold">Good {greet()}, {state.user?.name || "Farmer"}! 👋</h1>
              <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                <MapPin className="w-4 h-4" />
                <span>{state.farm?.district || "Location"}, {state.farm?.state || "State"}</span>
              </div>
            </div>
            <Badge variant="secondary" className="flex items-center gap-1">
              <Wifi className="w-3 h-3" />
              Online
            </Badge>
          </div>

          {wx && (
            <div className="bg-background/60 backdrop-blur rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Sun className="w-8 h-8 text-yellow-500" />
                  <div>
                    <div className="text-3xl font-bold">{Math.round(wx.current.temperature_c)}°C</div>
                    <div className="text-sm text-muted-foreground">
                      Humidity {wx.current.humidity_pct || 0}%
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">Next 7 days</div>
                  <div className="text-xs text-muted-foreground">
                    {wx.next24h_total_rain_mm !== undefined && `${wx.next24h_total_rain_mm}mm rain expected`}
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-2 gap-4">
        <Card 
          className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-primary/40"
          onClick={() => navigate("/ask")}
        >
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-3 bg-primary/10 rounded-full flex items-center justify-center">
              <Mic className="w-8 h-8 text-primary" />
            </div>
            <h3 className="font-semibold mb-1">Ask AI</h3>
            <p className="text-xs text-muted-foreground">Voice, text, or photo</p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-blue-400"
          onClick={() => navigate("/soil")}
        >
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-3 bg-blue-50 rounded-full flex items-center justify-center">
              <Sun className="w-8 h-8 text-blue-500" />
            </div>
            <h3 className="font-semibold mb-1">Weather</h3>
            <p className="text-xs text-muted-foreground">Local, next 7 days</p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-green-400"
          onClick={() => navigate("/disease")}
        >
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-3 bg-green-50 rounded-full flex items-center justify-center">
              <Camera className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="font-semibold mb-1">Crop Health</h3>
            <p className="text-xs text-muted-foreground">Upload photo of leaf</p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-secondary/40"
          onClick={() => navigate("/market")}
        >
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-3 bg-secondary/10 rounded-full flex items-center justify-center">
              <DollarSign className="w-8 h-8 text-secondary" />
            </div>
            <h3 className="font-semibold mb-1">Market Prices</h3>
            <p className="text-xs text-muted-foreground">Mandi rates nearby</p>
          </CardContent>
        </Card>
      </div>

      {/* Today's Recommendation */}
      {rc && rc.length > 0 && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Leaf className="w-5 h-5 text-primary" />
              Today's Recommendation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {rc.slice(0, 1).map((r) => (
                <div key={r.crop} className="p-4 bg-background rounded-xl border border-primary/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-lg">{r.crop}</span>
                    <Badge className="bg-primary text-primary-foreground">
                      {Math.round(r.probability * 100)}% Match
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Perfect conditions for planting now based on your location and soil
                  </p>
                </div>
              ))}
              <Button className="w-full" onClick={() => navigate("/crops")}>
                View Full Analysis →
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
