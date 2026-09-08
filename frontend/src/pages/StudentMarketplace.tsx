import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";


interface MarketplaceItem {
    id: number;
    description: string;
    price?: number;
    image_url?: string;
    contact_info?: string;
    status: "available" | "sold";
    seller_id: number;
}

interface NearbyShop {
    name: string;
    lat: number;
    lon: number;
    distance_km?: number;
}

const StudentMarketplace = () => {
    const { user } = useAuth();
    const userId = user?.id;
    const token = localStorage.getItem("access_token") || "";

    /* ---------------- STATES ---------------- */
    const [category, setCategory] = useState("others");
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [query, setQuery] = useState("");
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [items, setItems] = useState<MarketplaceItem[]>([]);
    const [shops, setShops] = useState<NearbyShop[]>([]);
    const [loading, setLoading] = useState(false);

    // Sell form
    const [showSellForm, setShowSellForm] = useState(false);
    const [description, setDescription] = useState("");
    const [price, setPrice] = useState("");
    const [contact, setContact] = useState("");
    const [image, setImage] = useState<File | null>(null);

    /* ---------------- LOAD DEFAULT ITEMS ---------------- */
    const loadItems = async () => {
        try {
            const res = await fetch(`/api/marketplace`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const data = await res.json();
            setItems(data || []);
        } catch {
            console.error("Failed to load marketplace items");
        }
    };

    useEffect(() => {
        loadItems();
    }, []);

    /* ---------------- AUTOCOMPLETE (LLM) ---------------- */
    useEffect(() => {
        const timer = setTimeout(async () => {
            if (query.trim().length < 2) {
                setSuggestions([]);
                return;
            }

            try {
                const res = await fetch(`/api/autocomplete`, {
                    method: "POST",
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
    const searchMarketplace = async () => {
        setSuggestions([]);
        setShowSuggestions(false); // ✅ hide dropdown when searching


        if (!query.trim()) {
            setShops([]);
            loadItems();
            return;
        }

        setLoading(true);
        setItems([]);
        setShops([]);

        try {
            const res = await fetch(`/api/marketplace/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ query }),
            });

            const data = await res.json();
            setItems(data.items || []);
            setShops(data.nearby_shops || []);
        } catch {
            alert("Marketplace search failed");
        } finally {
            setLoading(false);
        }
    };

    /* ---------------- STATUS TOGGLE ---------------- */
    const toggleStatus = async (itemId: number, status: string) => {
        const newStatus = status === "available" ? "sold" : "available";

        const res = await fetch(`/api/marketplace/${itemId}/status`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ status: newStatus }),
        });

        if (res.ok) loadItems();
        else alert("Failed to update status");
    };

    /* ---------------- POST ITEM ---------------- */
    const postItem = async () => {
        const formData = new FormData();
        formData.append("description", description);
        formData.append("category", category);
        formData.append("price", price);
        formData.append("contact", contact);
        if (image) formData.append("image", image);

        const res = await fetch(`/api/marketplace`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
        });

        if (res.ok) {
            setShowSellForm(false);
            setDescription("");
            setPrice("");
            setContact("");
            setImage(null);
            loadItems();
        } else {
            alert("Failed to post item");
        }
    };

    /* ---------------- UI ---------------- */
    return (
        <div className="space-y-6 p-4">

            {/* SEARCH */}
            <div className="relative">
                <div className="flex gap-2">
                    <input
                        className="border dark:border-gray-600 p-2 flex-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded"
                        placeholder="Search products or shops..."
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value);
                            setShowSuggestions(true); // ✅ user is typing
                        }}

                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                setShowSuggestions(false);
                                searchMarketplace();
                            }
                        }}

                    />
                    <button
                        onClick={searchMarketplace}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                    >
                        {loading ? <><Loader2 className="h-4 w-4 animate-spin mr-1 inline" />Searching...</> : "Search"}
                    </button>
                </div>

                {showSuggestions && suggestions.length > 0 && (

                    <ul className="absolute z-50 w-full bg-white dark:bg-gray-800 dark:border-gray-600 border rounded shadow mt-1">
                        {suggestions.map((s, i) => (
                            <li
                                key={i}
                                className="p-2 hover:bg-blue-50 dark:hover:bg-gray-700 dark:text-white cursor-pointer text-sm"
                                onClick={() => {
                                    setQuery(s);
                                    setSuggestions([]);
                                    setShowSuggestions(false); // ✅ stop autocomplete
                                }}

                            >
                                {s}
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* SELL */}
            <button
                className="bg-green-600 text-white px-4 py-2 rounded"
                onClick={() => setShowSellForm(!showSellForm)}
            >
                {showSellForm ? "Cancel" : "Sell Product"}
            </button>

            {showSellForm && (
                <div className="border dark:border-gray-600 p-4 rounded space-y-3 bg-gray-50 dark:bg-gray-800">
                    <input className="border dark:border-gray-600 p-2 w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
                    <select
                        className="border dark:border-gray-600 p-2 w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                    >
                        <option value="sports">Sports</option>
                        <option value="electronics">Electronics</option>
                        <option value="food">Food</option>
                        <option value="cloth">Cloth</option>
                        <option value="books">Books</option>
                        <option value="others">Others</option>
                    </select>
                    <input className="border dark:border-gray-600 p-2 w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded" placeholder="Price" value={price} onChange={(e) => setPrice(e.target.value)} />
                    <input className="border dark:border-gray-600 p-2 w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded" placeholder="Contact / Room No." value={contact} onChange={(e) => setContact(e.target.value)} />
                    <input type="file" accept="image/png,image/jpeg" onChange={(e) => setImage(e.target.files?.[0] || null)} />
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded" onClick={postItem}>Post Item</button>
                </div>
            )}

            {/* LISTINGS */}
            <div>
                <h2 className="text-lg font-semibold dark:text-white">Marketplace Listings</h2>

                {loading && <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mt-2"><Loader2 className="h-4 w-4 animate-spin" />Searching marketplace...</div>}
            {items.length === 0 && !loading && <p className="text-sm text-gray-500 dark:text-gray-400">No listings found</p>}

                <ul className="space-y-4 mt-3">
                    {items.map((item) => (
                        <li key={item.id} className="border dark:border-gray-600 p-4 rounded space-y-1 bg-white dark:bg-gray-800 dark:text-white">
                            <p className="font-medium">{item.description}</p>
                            {item.price && <p className="text-sm">₹ {item.price}</p>}
                            {item.contact_info && <p className="text-sm">📞 {item.contact_info}</p>}
                            {item.image_url && (
                                <img
                                    src={item.image_url}
                                    className="w-40 rounded mt-2"
                                />
                            )}

                            {item.seller_id === userId ? (
                                <button
                                    onClick={() => toggleStatus(item.id, item.status)}
                                    className={`px-3 py-1 text-white rounded text-sm ${item.status === "available" ? "bg-green-600" : "bg-red-600"
                                        }`}
                                >
                                    {item.status}
                                </button>
                            ) : (
                                <span className="text-sm text-gray-600 dark:text-gray-300">Status: {item.status}</span>
                            )}
                        </li>
                    ))}
                </ul>
            </div>

            {/* SHOPS */}
            {shops.length > 0 && (
                <div>
                    <h2 className="text-lg font-semibold dark:text-white">Nearby Shops</h2>
                    <ul className="space-y-3 mt-2">
                        {shops.map((s, i) => (
                            <li key={i} className="border dark:border-gray-600 p-3 rounded bg-white dark:bg-gray-800 dark:text-white">
                                <b>{s.name}</b>
                                {s.distance_km && <p>{s.distance_km} km away</p>}
                                <a
                                    href={`https://www.google.com/maps?q=${s.lat},${s.lon}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-blue-600 underline text-sm"
                                >
                                    Open in Maps
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default StudentMarketplace;
