import { useEffect, useState } from "react";
import { useApp } from "../lib/store";
import { recos, type CropReco } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Loader2, Sprout } from "lucide-react";

const STALE_MS = 30 * 60 * 1000; // 30 minutes

export default function CropsPage() {
  const { state, dispatch } = useApp();
  const coords = state.farm ? { lat: state.farm.latitude, lon: state.farm.longitude } : null;
  const [loading, setLoading] = useState(false);

  // Check if we have cached recommendations
  const cachedRecos = state.recoCache.data;
  const cacheAge = state.recoCache.ts ? Date.now() - state.recoCache.ts : Infinity;
  const isStale = cacheAge > STALE_MS;

  useEffect(() => {
    // Use cache if available and not stale
    if (cachedRecos && !isStale) return;
    
    if (!state.user || !coords) return;
    
    setLoading(true);
    recos.crops({ userId: state.user.id, coords })
      .then((data) => {
        dispatch({ type: "SET_RECO", payload: { key: state.user!.id, data } });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [state.user?.id, coords?.lat, coords?.lon]);

  const list = cachedRecos || [];

  if (!state.user || !state.farm) {
    return (
      <div className="mx-auto max-w-3xl p-4">
        <Card>
          <CardContent className="p-8 text-center">
            <Sprout className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="font-semibold mb-2">Complete Your Profile</h3>
            <p className="text-muted-foreground">Please complete your profile and farm details to get crop recommendations.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl p-4 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Crop Recommendations</h1>
        <p className="text-muted-foreground">AI-powered suggestions based on your location and soil conditions</p>
      </div>

      {loading && (
        <Card>
          <CardContent className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-muted-foreground">Analyzing your farm conditions...</p>
          </CardContent>
        </Card>
      )}

      {!loading && list.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">No recommendations available at this time.</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {list.map((r, idx) => (
          <Card key={r.crop} className={idx === 0 ? "border-2 border-primary" : ""}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Sprout className="w-5 h-5 text-primary" />
                  {r.crop}
                </CardTitle>
                {idx === 0 && <Badge>Best Match</Badge>}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-muted-foreground">Suitability Score</span>
                    <span className="font-medium">{(r.probability * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={r.probability * 100} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
