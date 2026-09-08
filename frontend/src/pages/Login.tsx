import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "@/hooks/use-toast";

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ email: "", password: "" });

  // Auto-fill + auto-submit if coming from quick login
  useEffect(() => {
    const state = location.state as { email?: string; password?: string } | null;
    if (state?.email && state?.password) {
      setFormData({ email: state.email, password: state.password });
      // slight delay so the UI renders first
      setTimeout(() => handleAutoLogin(state.email!, state.password!), 300);
    }
  }, []);

  const handleAutoLogin = async (email: string, password: string) => {
    setLoading(true);
    try {
      const success = await login(email, password);
      if (success) {
        toast({ title: "Login successful", description: "Welcome back!" });
        navigate("/dashboard");
      } else {
        toast({ title: "Login failed", description: "Invalid credentials", variant: "destructive" });
      }
    } catch {
      toast({ title: "Error", description: "Something went wrong", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await handleAutoLogin(formData.email, formData.password);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Login</CardTitle>
          <CardDescription>Enter your credentials to access your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="your.email@example.com"
                required
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="••••••••"
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </Button>
          </form>

          <div className="mt-4 text-center space-y-1">
            <Button variant="link" onClick={() => navigate("/signup")}>
              Don't have an account? Sign up
            </Button>
            <br />
            <Button variant="link" onClick={() => navigate("/")}>
              Back to home
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
