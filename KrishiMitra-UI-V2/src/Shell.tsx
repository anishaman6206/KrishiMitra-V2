import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Home, Leaf, BarChart3, User, Sprout, Bug } from "lucide-react";

type ShellProps = {
  children: React.ReactNode;
};

export default function Shell({ children }: ShellProps) {
  const location = useLocation();
  
  const navItems = [
    { to: "/home", label: "Home", icon: Home },
    { to: "/crops", label: "Crops", icon: Leaf },
    { to: "/soil", label: "Soil", icon: Sprout },
    { to: "/market", label: "Market", icon: BarChart3 },
    { to: "/disease", label: "Disease", icon: Bug },
    { to: "/profile", label: "Profile", icon: User },
  ];

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-3">
      <header className="mb-4 flex items-center justify-between">
        <Link to="/home" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
            <span className="text-white font-bold text-sm">KM</span>
          </div>
          <span className="text-lg font-semibold">KrishiMitra</span>
        </Link>
        <nav className="hidden gap-4 text-sm md:flex">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
                  location.pathname === item.to
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
                to={item.to}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>

      <main>{children}</main>
    </div>
  );
}

export function TabBar() {
  const location = useLocation();
  
  const navItems = [
    { to: "/home", label: "Home", icon: Home },
    { to: "/crops", label: "Crops", icon: Leaf },
    { to: "/soil", label: "Soil", icon: Sprout },
    { to: "/market", label: "Market", icon: BarChart3 },
    { to: "/profile", label: "Profile", icon: User },
  ];

  return (
    <nav className="sticky bottom-0 flex border-t bg-background md:hidden">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.to;
        return (
          <Link
            key={item.to}
            to={item.to}
            className={`flex-1 flex flex-col items-center justify-center py-2 text-xs ${
              isActive ? "text-primary font-semibold" : "text-muted-foreground"
            }`}
          >
            <Icon className="h-5 w-5 mb-1" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
