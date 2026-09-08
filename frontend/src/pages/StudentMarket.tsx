import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";


interface NearbyShop {
    name: string;
    lat: number;
    lon: number;
    distance_km?: number;
}

const StudentMarket = () => {
    const token = localStorage.getItem(`access_token`) || ``;

    /* ---------------- STATES ---------------- */
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [query, setQuery] = useState(``);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [results, setResults] = useState<NearbyShop[]>([]);
    const [category, setCategory] = useState<string>(``);
    const [confidence, setConfidence] = useState<number | undefined>(undefined);
    const [loading, setLoading] = useState(false);

    /* ---------------- AUTOCOMPLETE (LLM) ---------------- */
    useEffect(() => {
        const timer = setTimeout(async () => {
            if (query.trim().length < 2) {
                setSuggestions([]);
                return;
            }

            try {
                const res = await fetch(`/api/autocomplete`, {
                    method: `POST`,
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({ query }),
                });

                if (res.ok) {
                    const data = await res.json();
                    setSuggestions(data.suggestions || []);
                }
            } catch {
                setSuggestions([]);
            }
        }, 400);

        return () => clearTimeout(timer);
    }, [query]);

    /* ---------------- SEARCH ---------------- */
    const handleSearch = async () => {
        setSuggestions([]);
        setShowSuggestions(false);


        if (!query.trim()) return;

        setLoading(true);
        setResults([]);
        setCategory(``);
        setConfidence(undefined);

        try {
            const res = await fetch(`/api/student/nearby-shops`, {
                method: `POST`,
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ query }),
            });

            const data = await res.json();

            setCategory(data.category || ``);
            setConfidence(data.confidence);

            const sorted = (data.results || []).sort(
                (a: NearbyShop, b: NearbyShop) =>
                    (a.distance_km ?? Infinity) - (b.distance_km ?? Infinity)
            );

            setResults(sorted);
        } catch {
            alert(`Failed to search nearby shops`);
        } finally {
            setLoading(false);
        }
    };

    /* ---------------- UI ---------------- */
    return (
        <div className="space-y-4">

            {/* SEARCH BAR */}
            <div className="relative">
                <div className="flex gap-2">
                    <input
                        className="border p-2 flex-1 bg-background text-foreground dark:bg-gray-800 dark:text-white dark:border-gray-600 rounded"
                        placeholder="Search products or shops..."
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value);
                            setShowSuggestions(true);
                        }}

                        onKeyDown={(e) => {
                            if (e.key === `Enter`) {
                                setShowSuggestions(false);
                                handleSearch();
                            }
                        }}

                    />
                    <button
                        onClick={handleSearch}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                    >
                        Search
                    </button>
                </div>

                {/* AUTOCOMPLETE */}
                {showSuggestions && suggestions.length > 0 && (

                    <ul className="absolute z-50 w-full bg-white dark:bg-gray-800 dark:border-gray-600 border rounded shadow mt-1">
                        {suggestions.map((s, i) => (
                            <li
                                key={i}
                                className="p-2 hover:bg-blue-50 dark:hover:bg-gray-700 dark:text-white cursor-pointer text-sm"
                                onClick={() => {
                                    setQuery(s);
                                    setSuggestions([]);
                                    setShowSuggestions(false);
                                }}

                            >
                                {s}
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* STATUS */}
            {loading && <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300"><Loader2 className="h-4 w-4 animate-spin" />Searching nearby shops...</div>}

            {category && (
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    Category: <b>{category}</b>
                    {typeof confidence === `number` && (
                        <span> (confidence: {confidence.toFixed(2)})</span>
                    )}
                </p>
            )}

            {/* RESULTS */}
            <ul className="space-y-3">
                {results.map((r, i) => (
                    <li
                        key={i}
                        className="border dark:border-gray-600 p-4 rounded-md bg-white dark:bg-gray-800 dark:text-white"
                    >
                        <div className="font-semibold text-lg">{r.name || `Unnamed Shop`}</div>

                        {typeof r.distance_km === `number` && (
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                                📍 {r.distance_km.toFixed(2)} km away
                            </div>
                        )}

                        <a
                            href={`https://www.google.com/maps?q=${r.lat},${r.lon}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 text-sm underline mt-1 inline-block"
                        >
                            Open in Google Maps
                        </a>
                    </li>
                ))}
            </ul>

        </div>
    );
};

export default StudentMarket;
