export default function Footer() {
  return (
    <footer className="w-full border-t border-border bg-background mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-muted-foreground">
        <span>© {new Date().getFullYear()} DormOS-IIITN. All rights reserved.</span>
        <span>Built for hostel management</span>
      </div>
    </footer>
  );
}
