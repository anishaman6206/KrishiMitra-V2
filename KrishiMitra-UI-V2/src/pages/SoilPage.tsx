import { useEffect, useState } from "react";
import { useApp } from "../lib/store";
import { weather, soil, type WeatherResponse, type SoilResponse } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Sun, Droplets, CloudRain } from "lucide-react";

export default function SoilPage() {
  const { state } = useApp();
  const coords = state.farm ? { lat: state.farm.latitude, lon: state.farm.longitude } : null;
  const [wx, setWx] = useState<WeatherResponse | null>(null);
  const [sg, setSg] = useState<SoilResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!coords) return;
    setLoading(true);
    (async () => {
      const [w, s] = await Promise.all([weather.get(coords), soil.get(coords)]);
      setWx(w);
      setSg(s);
    })()
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [state.farm]);

  return (
    <div className="mx-auto max-w-5xl p-4 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Weather & Soil Analytics</h1>
        <p className="text-muted-foreground">Comprehensive environmental data for your farm</p>
      </div>

      {loading && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center space-x-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <span className="text-sm text-muted-foreground">Loading data...</span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sun className="h-5 w-5 text-primary" />
              Weather Conditions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {wx ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                    <div className="flex items-center gap-2 mb-1">
                      <Sun className="h-4 w-4 text-primary" />
                      <span className="text-xs text-muted-foreground">Temperature</span>
                    </div>
                    <div className="text-2xl font-bold text-primary">
                      {wx.current.temperature_c}°C
                    </div>
                  </div>

                  <div className="p-4 bg-muted rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <Droplets className="h-4 w-4 text-blue-500" />
                      <span className="text-xs text-muted-foreground">Humidity</span>
                    </div>
                    <div className="text-2xl font-bold">{wx.current.humidity_pct ?? 0}%</div>
                  </div>
                </div>

                {typeof wx.current.rain_mm === "number" && (
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <CloudRain className="h-4 w-4 text-blue-600" />
                      <span className="text-sm text-muted-foreground">Rainfall</span>
                    </div>
                    <div className="text-xl font-bold">{wx.current.rain_mm} mm</div>
                  </div>
                )}

                <div className="text-xs text-muted-foreground">
                  Current conditions updated
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No weather data available</div>
            )}
          </CardContent>
        </Card>

        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Droplets className="h-5 w-5 text-primary" />
              Soil Health (Topsoil)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sg?.topsoil ? (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">pH Level</span>
                    <span className="text-lg font-bold text-primary">{sg.topsoil.ph_h2o.toFixed(1)}</span>
                  </div>
                  <Progress value={(sg.topsoil.ph_h2o / 14) * 100} className="h-2" />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Soil Organic Carbon</span>
                    <span className="text-lg font-bold text-primary">{sg.topsoil.soc_g_per_kg} g/kg</span>
                  </div>
                  <Progress value={(sg.topsoil.soc_g_per_kg / 100) * 100} className="h-2" />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Nitrogen</span>
                    <span className="text-lg font-bold text-primary">
                      {sg.topsoil.nitrogen_g_per_kg.toFixed(1)} g/kg
                    </span>
                  </div>
                  <Progress value={Math.min(sg.topsoil.nitrogen_g_per_kg, 100)} className="h-2" />
                </div>

                <div className="grid grid-cols-2 gap-3 mt-4">
                  <div className="p-3 bg-muted rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Clay</div>
                    <div className="text-lg font-bold">{sg.topsoil.clay_g_per_kg?.toFixed(1) || '—'} g/kg</div>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Sand</div>
                    <div className="text-lg font-bold">{sg.topsoil.sand_g_per_kg?.toFixed(1) || '—'} g/kg</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No soil data available</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
