import { useState } from "react";
import { useApp } from "../lib/store";
import { market, type MarketPrice, type ForecastPack } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, DollarSign, BarChart3 } from "lucide-react";

export default function MarketPage() {
  const { state } = useApp();
  const defaultDistrict = state.farm?.district || "";

  return (
    <div className="mx-auto max-w-6xl p-4 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Market Intelligence</h1>
        <p className="text-muted-foreground">Real-time prices and AI-powered forecasts for better trading decisions</p>
      </div>

      <Tabs defaultValue="prices" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="prices">Current Prices</TabsTrigger>
          <TabsTrigger value="forecast">Forecast</TabsTrigger>
        </TabsList>

        <TabsContent value="prices">
          <PricesPanel defaultDistrict={defaultDistrict} />
        </TabsContent>

        <TabsContent value="forecast">
          <ForecastPanel defaultDistrict={defaultDistrict} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function fmtINR(n: number | string) {
  const num = typeof n === "number" ? n : Number(n);
  if (!isFinite(num)) return "₹—";
  return "₹" + num.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

/* ---------------- Current Prices ---------------- */

function PricesPanel({ defaultDistrict }: { defaultDistrict: string }) {
  const [district, setDistrict] = useState(defaultDistrict);
  const [commodity, setCommodity] = useState("");
  const [mandi, setMandi] = useState("");
  const [rows, setRows] = useState<MarketPrice[] | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await market.prices({
        district: district || undefined,
        commodity: commodity || undefined,
        mandi: mandi || undefined,
      });
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="border-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-primary" />
          Current Market Prices
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-4">
          <Input placeholder="District" value={district} onChange={(e) => setDistrict(e.target.value)} />
          <Input placeholder="Commodity (optional)" value={commodity} onChange={(e) => setCommodity(e.target.value)} />
          <Input placeholder="Mandi (optional)" value={mandi} onChange={(e) => setMandi(e.target.value)} />
          <Button onClick={load} disabled={loading}>
            {loading ? "Loading..." : "Fetch Prices"}
          </Button>
        </div>

        <div className="overflow-x-auto rounded-lg border">
          {!rows ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              Enter a district and click Fetch to see market prices
            </div>
          ) : rows.length === 0 ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              No results found for the selected filters
            </div>
          ) : (
            <table className="min-w-full text-sm">
              <thead className="bg-muted/50 text-left">
                <tr>
                  <th className="p-3 font-semibold">Commodity</th>
                  <th className="p-3 font-semibold">Mandi • District</th>
                  <th className="p-3 font-semibold text-right">Price</th>
                  <th className="p-3 font-semibold text-right">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {rows.map((r, i) => (
                  <tr key={`${r.commodity}-${r.mandi}-${i}`} className="hover:bg-muted/30 transition-colors">
                    <td className="p-3 font-semibold">{r.commodity}</td>
                    <td className="p-3 text-muted-foreground">
                      {r.mandi}
                      {r.district ? `, ${r.district}` : ""}
                    </td>
                    <td className="p-3 text-right">
                      <span className="font-bold text-lg">{fmtINR(r.price)}</span>
                      <span className="text-xs text-muted-foreground ml-1">/ {r.unit || "Quintal"}</span>
                    </td>
                    <td className="p-3 text-right text-muted-foreground text-xs">{r.lastUpdated || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/* ---------------- Forecast ---------------- */

function ForecastPanel({ defaultDistrict }: { defaultDistrict: string }) {
  const [commodity, setCommodity] = useState("");
  const [district, setDistrict] = useState(defaultDistrict);
  const [mandi, setMandi] = useState("");
  const [pack, setPack] = useState<ForecastPack | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await market.forecast({
        commodity,
        district: district || undefined,
        mandi: mandi || undefined,
        horizon_days: 7,
      });
      setPack(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="border-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          Price Forecast
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-5">
          <Input className="md:col-span-2" placeholder="Commodity" value={commodity} onChange={(e) => setCommodity(e.target.value)} />
          <Input placeholder="District (optional)" value={district} onChange={(e) => setDistrict(e.target.value)} />
          <Input placeholder="Mandi (optional)" value={mandi} onChange={(e) => setMandi(e.target.value)} />
          <Button onClick={load} disabled={loading}>
            {loading ? "Forecasting..." : "Get Forecast"}
          </Button>
        </div>

        <div className="overflow-x-auto rounded-lg border">
          {!pack ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              Enter a commodity and click Get Forecast to see price predictions
            </div>
          ) : (
            <div className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">{pack.context.commodity}</h3>
                  <p className="text-xs text-muted-foreground">
                    Showing <span className="font-medium">Min / Modal / Max</span> forecasts (₹/quintal)
                  </p>
                </div>
                <Badge variant="outline">AI Forecast</Badge>
              </div>

              <table className="min-w-full text-sm">
                <thead className="bg-muted/50 text-left">
                  <tr>
                    <th className="p-3 font-semibold">Date</th>
                    <th className="p-3 font-semibold text-right">
                      <div className="flex items-center justify-end gap-1">
                        <TrendingDown className="h-3 w-3 text-destructive" />
                        Min
                      </div>
                    </th>
                    <th className="p-3 font-semibold text-right">Modal</th>
                    <th className="p-3 font-semibold text-right">
                      <div className="flex items-center justify-end gap-1">
                        <TrendingUp className="h-3 w-3 text-success" />
                        Max
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {pack.forecast.map((r, i) => {
                    const min = r.p20_adj ?? r.p20;
                    const mid = r.p50_adj ?? r.p50;
                    const max = r.p80_adj ?? r.p80;
                    return (
                      <tr key={i} className="hover:bg-muted/30 transition-colors">
                        <td className="p-3 font-medium">{r.date}</td>
                        <td className="p-3 text-right">
                          {fmtINR(min)}
                          <span className="text-xs text-muted-foreground ml-1">/ quintal</span>
                        </td>
                        <td className="p-3 text-right">
                          <span className="font-bold text-primary">{fmtINR(mid)}</span>
                          <span className="text-xs text-muted-foreground ml-1">/ quintal</span>
                        </td>
                        <td className="p-3 text-right">
                          {fmtINR(max)}
                          <span className="text-xs text-muted-foreground ml-1">/ quintal</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
