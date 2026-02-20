import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "@/lib/store";
import { ensureUserAndFarm, geocodeFromBrowser } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Leaf, Globe, MapPin, Check, ArrowLeft, Loader2, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import onboardingImage from "@/assets/onboarding-farmer.png";

export default function Index() {
  const navigate = useNavigate();
  const { state, dispatch } = useApp();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);

  // Language selection
  const [language, setLanguage] = useState("en");

  // Personal info
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [mobile, setMobile] = useState("");
  const [village, setVillage] = useState("");
  const [district, setDistrict] = useState("");
  const [stateName, setStateName] = useState("");
  const [farmSize, setFarmSize] = useState("");

  // Farm info
  const [crops, setCrops] = useState("");
  const [experience, setExperience] = useState("");
  const [soilType, setSoilType] = useState("");

  // GPS method
  const [useGPS, setUseGPS] = useState(false);

  useEffect(() => {
    if (state.user && state.farm) {
      navigate("/home");
    }
  }, [state.user, state.farm, navigate]);

  const languages = [
    { code: "en", name: "English", native: "English", icon: "🇬🇧" },
    { code: "hi", name: "Hindi", native: "हिंदी", icon: "🇮🇳" },
    { code: "bn", name: "Bengali", native: "বাংলা", icon: "🇮🇳" },
    { code: "te", name: "Telugu", native: "తెలుగు", icon: "🇮🇳" },
    { code: "mr", name: "Marathi", native: "मराठी", icon: "🇮🇳" },
    { code: "ta", name: "Tamil", native: "தமிழ்", icon: "🇮🇳" },
    { code: "ur", name: "Urdu", native: "اردو", icon: "🇵🇰" },
    { code: "gu", name: "Gujarati", native: "ગુજરાતી", icon: "🇮🇳" },
    { code: "kn", name: "Kannada", native: "ಕನ್ನಡ", icon: "🇮🇳" },
    { code: "pa", name: "Punjabi", native: "ਪੰਜਾਬੀ", icon: "🇮🇳" },
  ];

  const handleGPSClick = async () => {
    setGpsLoading(true);
    try {
      const coords = await geocodeFromBrowser();
      if (coords) {
        setUseGPS(true);
        toast.success("Location detected successfully!");
        // In production, you'd reverse geocode to get district/state
        // For now, user will still need to enter district/state manually
      } else {
        toast.error("Could not access GPS. Please enter manually.");
      }
    } catch (error) {
      toast.error("GPS access denied. Please enter manually.");
    } finally {
      setGpsLoading(false);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      const result = await ensureUserAndFarm({
        userName: name,
        mobile,
        language,
        farmName: `${name}'s Farm`,
        farmAreaHectares: Number(farmSize),
        location: `${village}, ${district}, ${stateName}`,
        district,
        state: stateName,
        rotation_history: crops.split(",").map(c => c.trim()).filter(Boolean),
      });

      dispatch({ type: "SET_USER", user: result.user });
      dispatch({ type: "SET_FARM", farm: result.farm });
      
      toast.success("Profile created successfully!");
      navigate("/home");
    } catch (error: any) {
      toast.error(error?.message || "Failed to create profile");
    } finally {
      setLoading(false);
    }
  };

  if (step === 0) {
    return (
      <>
        <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-sm border-0 shadow-lg">
            <CardContent className="pt-8 pb-6 space-y-6">
              <div className="text-center space-y-4">
                <div className="w-20 h-20 mx-auto bg-primary/10 rounded-3xl flex items-center justify-center">
                  <Leaf className="w-10 h-10 text-primary" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-primary mb-2">KrishiMitra AI</h1>
                  <p className="text-muted-foreground text-sm">Your AI farming assistant</p>
                </div>
                <div className="text-sm text-muted-foreground space-y-1 py-3">
                  <p>Smart crop recommendations • Weather insights</p>
                  <p>• Market prices</p>
                </div>
              </div>

              <div className="relative w-full aspect-video rounded-2xl overflow-hidden border-2 border-primary/10">
                <img 
                  src={onboardingImage} 
                  alt="Farmer in field" 
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="space-y-3">
                <Label className="flex items-center gap-2 text-base font-medium">
                  <Globe className="w-4 h-4 text-primary" />
                  Choose Your Language
                </Label>
                <Button
                  variant="outline"
                  onClick={() => setShowLanguageModal(true)}
                  className="w-full h-12 justify-between text-left border-2"
                >
                  <span>{languages.find(l => l.code === language)?.native || "English"}</span>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>

              <Button onClick={() => setStep(1)} size="lg" className="w-full h-14 text-base font-semibold">
                Get Started
                <ChevronRight className="ml-2 w-5 h-5" />
              </Button>

              <div className="flex justify-center gap-6 text-xs text-muted-foreground pt-2">
                <div className="flex items-center gap-1">
                  <Check className="w-3 h-3 text-green-600" />
                  Free to use
                </div>
                <div className="flex items-center gap-1">
                  <Check className="w-3 h-3 text-green-600" />
                  Secure & Private
                </div>
                <div className="flex items-center gap-1">
                  <Check className="w-3 h-3 text-green-600" />
                  Works offline
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Language Selection Modal */}
        <Dialog open={showLanguageModal} onOpenChange={setShowLanguageModal}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-primary" />
                Select Language
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => {
                    setLanguage(lang.code);
                    setShowLanguageModal(false);
                  }}
                  className={`w-full p-4 rounded-xl border-2 transition-all hover:border-primary/50 text-left ${
                    language === lang.code
                      ? "border-primary bg-primary/5"
                      : "border-muted"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{lang.icon}</span>
                      <div>
                        <div className="font-medium">{lang.native}</div>
                        <div className="text-xs text-muted-foreground">{lang.name}</div>
                      </div>
                    </div>
                    {language === lang.code && (
                      <Check className="w-5 h-5 text-primary" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </>
    );
  }

  if (step === 1) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 p-4">
        <div className="max-w-2xl mx-auto">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Leaf className="w-6 h-6 text-primary" />
                <span className="font-semibold text-lg">KrishiMitra AI</span>
              </div>
              <Button variant="ghost" size="sm">
                English
              </Button>
            </div>
          </div>

          <Card className="border-0 shadow-lg">
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl">Personal Information</CardTitle>
              <p className="text-sm text-muted-foreground">Tell us about yourself</p>
              
              {/* Progress indicator */}
              <div className="flex items-center gap-2 pt-4">
                <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
                  1
                </div>
                <div className="flex-1 h-1 bg-primary rounded" />
                <div className="w-10 h-10 rounded-full bg-muted text-muted-foreground flex items-center justify-center font-semibold">
                  2
                </div>
                <div className="flex-1 h-1 bg-muted rounded" />
                <div className="w-10 h-10 rounded-full bg-muted text-muted-foreground flex items-center justify-center font-semibold">
                  3
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
                💡 Tip: Use the GPS button to auto-fill your location
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your full name" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="age">Age *</Label>
                  <Input id="age" type="number" value={age} onChange={(e) => setAge(e.target.value)} placeholder="26" />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="mobile">Mobile Number *</Label>
                <div className="flex gap-2">
                  <Input className="w-20" value="+91" readOnly />
                  <Input id="mobile" value={mobile} onChange={(e) => setMobile(e.target.value)} placeholder="9876543210" />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="flex items-center gap-1">
                    <MapPin className="w-4 h-4 text-primary" />
                    Farm Location
                  </Label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant={useGPS ? "default" : "outline"}
                      onClick={handleGPSClick}
                      disabled={gpsLoading}
                    >
                      {gpsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <MapPin className="w-4 h-4" />}
                      GPS
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant={!useGPS ? "default" : "outline"}
                      onClick={() => setUseGPS(false)}
                    >
                      Manual
                    </Button>
                  </div>
                </div>
                
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-600">
                  You can use GPS for quick setup or enter your location manually below
                </div>

                <div className="space-y-3">
                  <Input value={village} onChange={(e) => setVillage(e.target.value)} placeholder="Enter your village name" />
                  <div className="grid grid-cols-2 gap-3">
                    <Input value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="District" />
                    <Input value={stateName} onChange={(e) => setStateName(e.target.value)} placeholder="Select state" />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="farmSize">Farm Size (acres/hectares) *</Label>
                <Input id="farmSize" type="number" step="0.1" value={farmSize} onChange={(e) => setFarmSize(e.target.value)} placeholder="2.5" />
              </div>

              <div className="flex gap-3 pt-4">
                <Button variant="outline" onClick={() => setStep(0)} size="lg" className="flex-1">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button 
                  onClick={() => setStep(2)} 
                  size="lg"
                  className="flex-1"
                  disabled={!name || !mobile || !district || !stateName || !farmSize}
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 p-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Leaf className="w-6 h-6 text-primary" />
              <span className="font-semibold text-lg">KrishiMitra AI</span>
            </div>
            <Button variant="ghost" size="sm">
              English
            </Button>
          </div>
        </div>

        <Card className="border-0 shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">Farm Information</CardTitle>
            <p className="text-sm text-muted-foreground">Tell us about your farming</p>
            
            {/* Progress indicator */}
            <div className="flex items-center gap-2 pt-4">
              <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center">
                <Check className="w-5 h-5" />
              </div>
              <div className="flex-1 h-1 bg-primary rounded" />
              <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
                2
              </div>
              <div className="flex-1 h-1 bg-primary rounded" />
              <div className="w-10 h-10 rounded-full bg-muted text-muted-foreground flex items-center justify-center font-semibold">
                3
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
              🌱 This helps us give you personalized crop recommendations
            </div>

            <div className="space-y-2">
              <Label htmlFor="crops" className="flex items-center gap-2">
                🌾 What crops do you grow? *
              </Label>
              <Input 
                id="crops" 
                value={crops} 
                onChange={(e) => setCrops(e.target.value)} 
                placeholder="Example: Rice, Wheat, Cotton, Tomatoes, Sugarcane"
              />
              <p className="text-xs text-muted-foreground">List the main crops you grow on your farm</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="experience" className="flex items-center gap-2">
                🚜 Your farming experience *
              </Label>
              <Input 
                id="experience" 
                value={experience} 
                onChange={(e) => setExperience(e.target.value)} 
                placeholder="How long have you been farming?"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="soilType" className="flex items-center gap-2">
                🌍 Your soil type
              </Label>
              <Select value={soilType} onValueChange={setSoilType}>
                <SelectTrigger>
                  <SelectValue placeholder="What type of soil do you have?" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="loamy">Loamy</SelectItem>
                  <SelectItem value="clay">Clay</SelectItem>
                  <SelectItem value="sandy">Sandy</SelectItem>
                  <SelectItem value="silt">Silt</SelectItem>
                  <SelectItem value="not-sure">Not Sure</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">Don't worry if you're not sure - we can help determine this later</p>
            </div>

            <div className="flex gap-3 pt-4">
              <Button variant="outline" onClick={() => setStep(1)} size="lg" className="flex-1">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Button 
                onClick={handleComplete}
                size="lg"
                className="flex-1"
                disabled={loading || !crops || !experience}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-2" />
                    Complete Setup
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
