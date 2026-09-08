import React from "react";
import { Building2, LogOut, User } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const isAuthPage =
    location.hash === "#/login" ||
    location.hash === "#/signup" ||
    location.pathname === "/login" ||
    location.pathname === "/signup";

  return (
    <header className="w-full bg-background border-b border-border shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <div
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => navigate("/")}
        >
          <Building2 className="h-7 w-7 text-primary" />
          <span className="text-xl font-bold text-foreground">DormOS-IIITN</span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <User className="h-4 w-4" />
                <span className="hidden sm:inline">{user.email}</span>
                <span className="capitalize bg-primary/10 text-primary text-xs px-2 py-0.5 rounded-full">
                  {user.role}
                </span>
              </div>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-1" />
                Logout
              </Button>
            </>
          ) : !isAuthPage ? (
            <Button size="sm" onClick={() => navigate("/login")}>
              Login
            </Button>
          ) : null}
        </div>
      </div>
    </header>
  );
}
