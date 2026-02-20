import { useState } from "react";
import { useApp } from "../lib/store";
import { ensureUserAndFarm } from "../lib/api";
import PreferencesCard from "../components/PreferencesCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { User, MapPin, Sprout, CheckCircle2, AlertCircle } from "lucide-react";

export default function ProfilePage() {
  const { state, dispatch } = useApp();
  const [name, setName] = useState(state.user?.name || "");
  const [mobile, setMobile] = useState(state.user?.mobile_number || "");
  const [lang, setLang] = useState(state.user?.language_pref || "en");

  const [farmName, setFarmName] = useState(state.farm?.name || "");
  const [farmArea, setFarmArea] = useState<number>(state.farm?.area_hectares || 1);
  const [district, setDistrict] = useState(state.farm?.district || "");
  const [stateName, setStateName] = useState(state.farm?.state || "");

  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMsg(null);
    setIsSuccess(false);
    try {
      const res = await ensureUserAndFarm({
        userName: name,
        mobile,
        language: lang,
        farmName,
        farmAreaHectares: farmArea,
        location: `${district}, ${stateName}`,
        district,
        state: stateName,
      });

      dispatch({ type: "SET_USER", user: res.user });
      dispatch({ type: "SET_FARM", farm: res.farm });
      setMsg("Profile saved successfully!");
      setIsSuccess(true);
      setTimeout(() => {
        setMsg(null);
        setIsSuccess(false);
      }, 3000);
    } catch (err: any) {
      setMsg(err?.message || "Failed to save profile");
      setIsSuccess(false);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-4 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Profile & Farm Details</h1>
        <p className="text-muted-foreground">Manage your personal information and farm configuration</p>
      </div>

      {msg && (
        <Alert variant={isSuccess ? "default" : "destructive"}>
          {isSuccess ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          <AlertDescription>{msg}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={onSave} className="space-y-6">
        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              Personal Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Name *</label>
                <Input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Your full name" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Mobile *</label>
                <Input value={mobile} onChange={(e) => setMobile(e.target.value)} required placeholder="Your mobile number" />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">Preferred Language *</label>
                <Select value={lang} onValueChange={setLang}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="hi">हिंदी</SelectItem>
                    <SelectItem value="bn">বাংলা</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sprout className="h-5 w-5 text-primary" />
              Farm Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Farm Name *</label>
                <Input value={farmName} onChange={(e) => setFarmName(e.target.value)} required placeholder="My Farm" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Farm Area (Hectares) *</label>
                <Input
                  type="number"
                  step="0.1"
                  value={farmArea}
                  onChange={(e) => setFarmArea(Number(e.target.value))}
                  required
                  placeholder="1.5"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-primary" />
              Location
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">District *</label>
                <Input value={district} onChange={(e) => setDistrict(e.target.value)} required placeholder="Your district" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">State *</label>
                <Input value={stateName} onChange={(e) => setStateName(e.target.value)} required placeholder="Your state" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Button type="submit" disabled={loading} size="lg" className="w-full">
          {loading ? (
            <>
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent mr-2" />
              Saving...
            </>
          ) : (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Save Profile
            </>
          )}
        </Button>
      </form>

      <PreferencesCard />
    </div>
  );
}
