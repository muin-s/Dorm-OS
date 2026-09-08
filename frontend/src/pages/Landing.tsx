import { Button } from "@/components/ui/button";
import { Building2, ShieldCheck, Wrench, GraduationCap } from "lucide-react";
import { useNavigate } from "react-router-dom";

const demoAccounts = [
  {
    role: "Student",
    icon: GraduationCap,
    email: "john@hostel.com",
    password: "john",
    color: "bg-blue-50 border-blue-200 hover:bg-blue-100 text-blue-700",
    iconColor: "text-blue-500",
  },
  {
    role: "Admin",
    icon: ShieldCheck,
    email: "admin@hostel.com",
    password: "admin",
    color: "bg-purple-50 border-purple-200 hover:bg-purple-100 text-purple-700",
    iconColor: "text-purple-500",
  },
  {
    role: "Repairer Staff",
    icon: Wrench,
    email: "ron@hostel.com",
    password: "ron",
    color: "bg-orange-50 border-orange-200 hover:bg-orange-100 text-orange-700",
    iconColor: "text-orange-500",
  },
];

const Landing = () => {
  const navigate = useNavigate();

  const handleQuickLogin = (email: string, password: string) => {
    navigate("/login", { state: { email, password } });
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative" style={{backgroundImage: "url(/frames.jpg)", backgroundSize: "cover", backgroundPosition: "center"}}>
      <div className="absolute inset-0 bg-black/60" /><div className="relative z-10 max-w-3xl w-full text-center space-y-8">

        {/* Icon + Title */}
        <div className="space-y-3">
          <div className="flex justify-center">
            <Building2 className="h-16 w-16 text-primary" />
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-white">
            DormOS-IIITN
          </h1>
          <p className="text-gray-200 text-lg max-w-xl mx-auto">
            A unified platform for students, administrators, and hostel staff to
            manage everything in one place.
          </p>
        </div>

        {/* Quick Login Section */}
        <div className="space-y-3">
          <p className="text-sm font-semibold text-gray-200 uppercase tracking-widest">
            Quick Demo Login
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {demoAccounts.map(({ role, icon: Icon, email, password, color, iconColor }) => (
              <button
                key={role}
                onClick={() => handleQuickLogin(email, password)}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all cursor-pointer ${color}`}
              >
                <Icon className={`h-7 w-7 ${iconColor}`} />
                <span className="font-semibold text-sm">Login as {role}</span>
                <span className="text-xs opacity-70">{email}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3 text-gray-200 text-sm">
          <div className="flex-1 border-t border-gray-400" />
          <span>or</span>
          <div className="flex-1 border-t border-gray-400" />
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button size="lg" onClick={() => navigate("/login")} className="text-base px-8">
            Login with your account
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={() => navigate("/signup")}
            className="text-base px-8"
          >
            Sign Up
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Landing;
