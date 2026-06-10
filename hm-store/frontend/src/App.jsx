import React, { useState, useEffect } from 'react';

// API Base URL (blank means relative path, works inside Docker reverse proxy)
const API_BASE = '';

export default function App() {
  // Navigation & Views
  const [currentView, setCurrentView] = useState('shop'); // 'shop', 'admin'
  const [selectedCategory, setSelectedCategory] = useState('All');
  
  // Data State
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState(['All', 'Men', 'Women', 'Divided', 'Kids', 'Accessories']);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Cart State
  const [cart, setCart] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  
  // Modals
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [authError, setAuthError] = useState('');
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  
  // User Session
  const [user, setUser] = useState(null); // { id, username, fullName, email, role }

  // Admin Stats
  const [stats, setStats] = useState({
    totalSales: 0,
    totalOrders: 0,
    totalCustomers: 0,
    totalProducts: 0,
    recentOrders: []
  });



  // Load products & check login
  useEffect(() => {
    fetchProducts();
    // Check localStorage for saved session
    const savedUser = localStorage.getItem('hm_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, [selectedCategory]);

  useEffect(() => {
    if (user && user.role === 'ADMIN') {
      fetchAdminStats();
    }
  }, [user, currentView]);

  const fetchProducts = async () => {
    try {
      const url = selectedCategory === 'All' 
        ? `${API_BASE}/api/products` 
        : `${API_BASE}/api/products?category=${selectedCategory}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      }
    } catch (err) {
      console.error('Error fetching products:', err);
    }
  };

  const fetchAdminStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setIsSearching(false);
      return;
    }
    setIsSearching(true);
    try {
      // Direct call to search endpoint (simulates search & log alerts)
      const res = await fetch(`${API_BASE}/api/products/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (res.ok) {
        setSearchResults(data);
      } else {
        // If SQL injection triggered database error, show error detail
        setSearchResults([]);
        alert(`Database Error Simulated!\nQuery: ${data.query}\nMessage: ${data.error}`);
      }
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      });
      const data = await res.json();
      if (res.ok) {
        setUser(data.user);
        localStorage.setItem('hm_user', JSON.stringify(data.user));
        setIsLoginOpen(false);
        setLoginForm({ username: '', password: '' });
      } else {
        setAuthError(data.error || 'Authentication failed');
      }
    } catch (err) {
      setAuthError('Connection server error');
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('hm_user');
    setCurrentView('shop');
  };

  // Cart Functions
  const addToCart = (product) => {
    setCart((prev) => {
      const existing = prev.find(item => item.product_id === product.product_id);
      if (existing) {
        if (existing.quantity >= product.stock) {
          alert(`Out of stock! Only ${product.stock} items available.`);
          return prev;
        }
        return prev.map(item => 
          item.product_id === product.product_id 
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [...prev, { ...product, quantity: 1 }];
    });
    
    // Auto-open cart drawer
    setIsCartOpen(true);
  };

  const updateCartQuantity = (productId, amount) => {
    setCart((prev) => {
      return prev.map(item => {
        if (item.product_id === productId) {
          const newQty = item.quantity + amount;
          const product = products.find(p => p.product_id === productId) || item;
          if (newQty > product.stock) {
            alert(`Only ${product.stock} items available.`);
            return item;
          }
          return newQty <= 0 ? null : { ...item, quantity: newQty };
        }
        return item;
      }).filter(Boolean);
    });
  };

  const handleCheckout = async () => {
    if (!user) {
      setIsCartOpen(false);
      setIsLoginOpen(true);
      return;
    }

    const totalAmount = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const orderPayload = {
      userId: user.id,
      items: cart.map(item => ({
        productId: item.product_id,
        quantity: item.quantity,
        price: item.price
      })),
      totalAmount
    };

    try {
      const res = await fetch(`${API_BASE}/api/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderPayload)
      });
      const data = await res.json();
      if (res.ok) {
        alert(`Order placed successfully!\nOrder ID: #${data.orderId}`);
        setCart([]);
        setIsCartOpen(false);
        fetchProducts(); // Refresh stock
      } else {
        alert(`Failed to place order: ${data.error}`);
      }
    } catch (err) {
      alert('Network error placing order');
    }
  };



  const formatPrice = (num) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(num);
  };

  const totalCartItems = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div class="min-h-screen flex flex-col bg-hm-light selection:bg-hm-red selection:text-white">
      {/* 1. HEADER */}
      <header class="sticky top-0 z-30 bg-white border-b border-hm-border">
        {/* Promotion bar */}
        <div class="bg-hm-dark text-white text-center py-2 text-xs font-semibold tracking-wider">
          FREE SHIPPING FOR ORDERS OVER 1,000,000 VND | MEMBER SPECIAL DESSERT
        </div>

        {/* Navigation */}
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div class="flex items-center space-x-10">
            {/* Logo H&M */}
            <div 
              onClick={() => { setCurrentView('shop'); setIsSearching(false); setSearchQuery(''); }} 
              class="cursor-pointer font-bold text-4xl text-hm-red font-serif tracking-tighter"
            >
              H&amp;M
            </div>

            {/* Menu options */}
            <nav class="hidden md:flex space-x-8 text-sm font-semibold tracking-wide uppercase">
              <span 
                onClick={() => { setCurrentView('shop'); setSelectedCategory('All'); setIsSearching(false); }}
                class={`cursor-pointer hover:text-hm-red transition-colors ${currentView === 'shop' && selectedCategory === 'All' ? 'text-hm-red border-b-2 border-hm-red pb-1' : 'text-hm-dark'}`}
              >
                Shop All
              </span>
              <span 
                onClick={() => { setCurrentView('shop'); setSelectedCategory('Women'); setIsSearching(false); }}
                class={`cursor-pointer hover:text-hm-red transition-colors ${currentView === 'shop' && selectedCategory === 'Women' ? 'text-hm-red border-b-2 border-hm-red pb-1' : 'text-hm-dark'}`}
              >
                Women
              </span>
              <span 
                onClick={() => { setCurrentView('shop'); setSelectedCategory('Men'); setIsSearching(false); }}
                class={`cursor-pointer hover:text-hm-red transition-colors ${currentView === 'shop' && selectedCategory === 'Men' ? 'text-hm-red border-b-2 border-hm-red pb-1' : 'text-hm-dark'}`}
              >
                Men
              </span>
              <span 
                onClick={() => { setCurrentView('shop'); setSelectedCategory('Divided'); setIsSearching(false); }}
                class={`cursor-pointer hover:text-hm-red transition-colors ${currentView === 'shop' && selectedCategory === 'Divided' ? 'text-hm-red border-b-2 border-hm-red pb-1' : 'text-hm-dark'}`}
              >
                Divided
              </span>
              {user && user.role === 'ADMIN' && (
                <span 
                  onClick={() => setCurrentView('admin')}
                  class={`cursor-pointer hover:text-hm-red transition-colors ${currentView === 'admin' ? 'text-hm-red border-b-2 border-hm-red pb-1' : 'text-hm-dark'}`}
                >
                  Admin Panel
                </span>
              )}

            </nav>
          </div>

          {/* Search, Cart, Auth */}
          <div class="flex items-center space-x-6">
            {/* Search Bar */}
            <form onSubmit={handleSearch} class="relative hidden sm:block">
              <input 
                type="text" 
                placeholder="Search products..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                class="w-60 pl-4 pr-10 py-1.5 bg-hm-light border border-transparent hover:border-hm-border focus:border-hm-dark focus:bg-white text-xs outline-none transition-all rounded"
              />
              <button type="submit" class="absolute right-3 top-2 text-hm-gray hover:text-hm-dark">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m21-21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                </svg>
              </button>
            </form>

            {/* Auth link */}
            {user ? (
              <div class="flex items-center space-x-4 text-xs font-semibold tracking-wide">
                <span class="text-hm-gray">Hi, <b class="text-hm-dark">{user.fullName}</b></span>
                <button onClick={handleLogout} class="text-hm-red hover:underline">Sign Out</button>
              </div>
            ) : (
              <button 
                onClick={() => setIsLoginOpen(true)}
                class="flex items-center space-x-1.5 text-xs font-semibold tracking-wide hover:text-hm-red transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                </svg>
                <span>Sign In</span>
              </button>
            )}

            {/* Cart Icon */}
            <button 
              onClick={() => setIsCartOpen(true)}
              class="relative p-1.5 hover:text-hm-red transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5.5 h-5.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 1 0-7.5 0v4.5m11.356-1.993 1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 0 1-1.12-1.243l1.264-12A1.125 1.125 0 0 1 5.513 7.5h12.974c.576 0 1.059.435 1.119 1.007ZM8.625 10.5a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm7.5 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
              </svg>
              {totalCartItems > 0 && (
                <span class="absolute -top-1 -right-1.5 bg-hm-red text-white text-[10px] w-4.5 h-4.5 flex items-center justify-center rounded-full font-bold">
                  {totalCartItems}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* 2. MAIN BODY */}
      <main class="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {currentView === 'shop' && (
          <div class="space-y-10">
            {/* HERO BANNER (Only shown on Shop All with no active search) */}
            {!isSearching && selectedCategory === 'All' && (
              <div class="relative bg-[#ebe8e3] rounded-lg overflow-hidden h-80 flex items-center">
                <div class="absolute inset-0 bg-cover bg-center opacity-30" style={{ backgroundImage: "url('https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&q=80')" }}></div>
                <div class="relative z-10 pl-12 max-w-lg space-y-4">
                  <span class="text-xs font-bold tracking-widest text-hm-red uppercase">Summer Arrival 2026</span>
                  <h1 class="text-5xl font-extrabold font-serif tracking-tight text-hm-dark leading-none">
                    DRESS FOR <br />THE MOMENT
                  </h1>
                  <p class="text-sm text-hm-gray max-w-md">
                    Explore high-quality, sustainable fabrics styled for dynamic modern lifestyles. Crafted under ethical fashion systems.
                  </p>
                  <div>
                    <button 
                      onClick={() => setSelectedCategory('Women')}
                      class="bg-hm-dark text-white hover:bg-hm-red text-xs font-bold tracking-wider px-6 py-3 uppercase transition-all rounded"
                    >
                      Explore Women
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* CATEGORY BAR */}
            <div class="flex items-center justify-between border-b border-hm-border pb-4">
              <div class="flex items-center space-x-2 overflow-x-auto scrollbar-hide py-1">
                {categories.map((cat) => (
                  <button 
                    key={cat}
                    onClick={() => { setSelectedCategory(cat); setIsSearching(false); setSearchQuery(''); }}
                    class={`px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all ${
                      selectedCategory === cat && !isSearching
                        ? 'bg-hm-dark text-white' 
                        : 'bg-white text-hm-dark border border-hm-border hover:bg-hm-light'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
              <div class="text-xs text-hm-gray">
                Showing {isSearching ? searchResults.length : products.length} items
              </div>
            </div>

            {/* SEARCH BANNER IF SEARCHING */}
            {isSearching && (
              <div class="bg-white p-4 rounded border border-hm-border flex items-center justify-between">
                <div>
                  <span class="text-xs text-hm-gray">Search results for:</span>
                  <h2 class="text-base font-bold text-hm-dark">"{searchQuery}"</h2>
                </div>
                <button 
                  onClick={() => { setIsSearching(false); setSearchQuery(''); }}
                  class="text-xs text-hm-red hover:underline font-semibold"
                >
                  Clear Search
                </button>
              </div>
            )}

            {/* PRODUCTS GRID */}
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
              {(isSearching ? searchResults : products).map((prod) => (
                <div 
                  key={prod.product_id}
                  class="group bg-white border border-hm-border rounded overflow-hidden flex flex-col hover:shadow-lg transition-all"
                >
                  {/* Image container */}
                  <div 
                    onClick={() => setSelectedProduct(prod)}
                    class="relative aspect-[3/4] bg-hm-light cursor-pointer overflow-hidden"
                  >
                    <img 
                      src={prod.image_url} 
                      alt={prod.name} 
                      class="object-cover w-full h-full group-hover:scale-105 transition-all duration-500"
                    />
                    {prod.stock === 0 && (
                      <span class="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center text-white text-xs font-bold uppercase tracking-wider">
                        Out of stock
                      </span>
                    )}
                    {prod.stock > 0 && prod.stock <= 5 && (
                      <span class="absolute top-2 left-2 bg-hm-red text-white text-[9px] font-bold px-2 py-0.5 rounded uppercase">
                        Low Stock ({prod.stock})
                      </span>
                    )}
                  </div>

                  {/* Body Info */}
                  <div class="p-4 flex-grow flex flex-col justify-between space-y-2">
                    <div>
                      <span class="text-[10px] text-hm-gray uppercase tracking-widest font-bold">
                        {prod.category_name}
                      </span>
                      <h3 
                        onClick={() => setSelectedProduct(prod)}
                        class="text-xs font-bold text-hm-dark group-hover:text-hm-red cursor-pointer line-clamp-1 transition-colors"
                      >
                        {prod.name}
                      </h3>
                      <p class="text-[11px] text-hm-gray line-clamp-2 mt-1">
                        {prod.description}
                      </p>
                    </div>

                    <div class="pt-2 flex items-center justify-between">
                      <span class="text-xs font-extrabold text-hm-dark">
                        {formatPrice(prod.price)}
                      </span>
                      
                      <button 
                        onClick={() => addToCart(prod)}
                        disabled={prod.stock === 0}
                        class={`p-1.5 rounded-full transition-all ${
                          prod.stock === 0 
                            ? 'bg-hm-border text-hm-gray cursor-not-allowed'
                            : 'bg-hm-dark text-white hover:bg-hm-red'
                        }`}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* NO PRODUCTS WARNING */}
            {(isSearching ? searchResults : products).length === 0 && (
              <div class="text-center py-20 bg-white border border-hm-border rounded space-y-4">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 mx-auto text-hm-gray">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 0 1 2.008 1.24l.885 1.77a2.25 2.25 0 0 0 2.007 1.24h1.98a2.25 2.25 0 0 0 2.007-1.24l.885-1.77a2.25 2.25 0 0 1 2.007-1.24h3.86m-18 0h18a2.25 2.25 0 0 1 2.25 2.25v4.5A2.25 2.25 0 0 1 21.75 21H2.25A2.25 2.25 0 0 1 0 18.75v-4.5A2.25 2.25 0 0 1 2.25 13.5Z" />
                </svg>
                <h3 class="text-sm font-bold text-hm-dark">No products found</h3>
                <p class="text-xs text-hm-gray">Try adjusting your category filters or search query.</p>
              </div>
            )}
          </div>
        )}

        {/* 3. ADMIN STATS PANEL */}
        {currentView === 'admin' && user && user.role === 'ADMIN' && (
          <div class="space-y-6">
            <h1 class="text-2xl font-bold tracking-tight text-hm-dark">H&amp;M Management Dashboard</h1>
            
            {/* Stat Cards */}
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="bg-white p-6 rounded border border-hm-border shadow-sm">
                <span class="text-xs text-hm-gray font-semibold block uppercase">Total Revenue</span>
                <span class="text-xl font-extrabold text-hm-dark block mt-2">{formatPrice(stats.totalSales)}</span>
              </div>
              <div class="bg-white p-6 rounded border border-hm-border shadow-sm">
                <span class="text-xs text-hm-gray font-semibold block uppercase">Orders Received</span>
                <span class="text-xl font-extrabold text-hm-dark block mt-2">{stats.totalOrders}</span>
              </div>
              <div class="bg-white p-6 rounded border border-hm-border shadow-sm">
                <span class="text-xs text-hm-gray font-semibold block uppercase">Active Customers</span>
                <span class="text-xl font-extrabold text-hm-dark block mt-2">{stats.totalCustomers}</span>
              </div>
              <div class="bg-white p-6 rounded border border-hm-border shadow-sm">
                <span class="text-xs text-hm-gray font-semibold block uppercase">Product Catalog</span>
                <span class="text-xl font-extrabold text-hm-dark block mt-2">{stats.totalProducts} items</span>
              </div>
            </div>

            {/* Recent Orders */}
            <div class="bg-white rounded border border-hm-border shadow-sm overflow-hidden">
              <div class="px-6 py-4 border-b border-hm-border bg-hm-light flex justify-between items-center">
                <h3 class="text-sm font-bold text-hm-dark uppercase tracking-wider">Recent Orders Log</h3>
                <button onClick={fetchAdminStats} class="text-xs text-hm-red hover:underline font-semibold">Refresh</button>
              </div>
              <div class="overflow-x-auto">
                <table class="min-w-full text-xs text-left text-hm-dark">
                  <thead class="bg-hm-light font-bold text-hm-gray uppercase border-b border-hm-border">
                    <tr>
                      <th class="px-6 py-3">Order ID</th>
                      <th class="px-6 py-3">Customer</th>
                      <th class="px-6 py-3">Date</th>
                      <th class="px-6 py-3">Total Amount</th>
                      <th class="px-6 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-hm-border">
                    {stats.recentOrders.map((ord) => (
                      <tr key={ord.order_id} class="hover:bg-hm-light transition-colors">
                        <td class="px-6 py-4 font-semibold text-hm-red">#{ord.order_id}</td>
                        <td class="px-6 py-4">{ord.username}</td>
                        <td class="px-6 py-4">{new Date(ord.created_at).toLocaleString()}</td>
                        <td class="px-6 py-4 font-bold">{formatPrice(ord.total_amount)}</td>
                        <td class="px-6 py-4">
                          <span class={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            ord.status === 'Completed' ? 'bg-green-100 text-green-700' :
                            ord.status === 'Processing' ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {ord.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {stats.recentOrders.length === 0 && (
                      <tr>
                        <td colSpan="5" class="text-center py-8 text-hm-gray">No orders recorded in database yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}


      </main>

      {/* 3. FOOTER */}
      <footer class="bg-white border-t border-hm-border mt-16 py-12 text-xs text-hm-gray">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-4 gap-8">
          <div class="space-y-3">
            <h4 class="font-bold text-hm-dark uppercase tracking-wider">Shop</h4>
            <ul class="space-y-2">
              <li class="hover:underline cursor-pointer">Women</li>
              <li class="hover:underline cursor-pointer">Men</li>
              <li class="hover:underline cursor-pointer">Divided</li>
              <li class="hover:underline cursor-pointer">Kids</li>
            </ul>
          </div>
          <div class="space-y-3">
            <h4 class="font-bold text-hm-dark uppercase tracking-wider">Corporate Info</h4>
            <ul class="space-y-2">
              <li class="hover:underline cursor-pointer">Career at H&amp;M</li>
              <li class="hover:underline cursor-pointer">About H&amp;M group</li>
              <li class="hover:underline cursor-pointer">Sustainability H&amp;M Group</li>
              <li class="hover:underline cursor-pointer">Investor relations</li>
            </ul>
          </div>
          <div class="space-y-3">
            <h4 class="font-bold text-hm-dark uppercase tracking-wider">Help</h4>
            <ul class="space-y-2">
              <li class="hover:underline cursor-pointer">Customer Service</li>
              <li class="hover:underline cursor-pointer">My Account</li>
              <li class="hover:underline cursor-pointer">Store Locator</li>
              <li class="hover:underline cursor-pointer">Legal &amp; Privacy</li>
            </ul>
          </div>
          <div class="space-y-3">
            <h4 class="font-bold text-hm-dark uppercase tracking-wider">About Us</h4>
            <p class="leading-relaxed">
              H&amp;M is a fashion brand, offering the latest styles and inspiration for all. Happy shopping!
            </p>
          </div>
        </div>
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12 pt-6 border-t border-hm-border flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
          <p>&copy; 2026 H&amp;M Hennes &amp; Mauritz AB. All rights reserved.</p>
          <div class="font-bold text-hm-red tracking-widest font-serif text-lg">H&amp;M</div>
        </div>
      </footer>

      {/* 4. PRODUCT DETAIL MODAL */}
      {selectedProduct && (
        <div class="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4 bg-black bg-opacity-50 animate-fade-in">
          <div class="bg-white rounded max-w-2xl w-full overflow-hidden shadow-2xl relative border border-hm-border animate-slide-up">
            <button 
              onClick={() => setSelectedProduct(null)}
              class="absolute top-4 right-4 text-hm-dark hover:text-hm-red z-10 p-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5.5 h-5.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>

            <div class="grid grid-cols-1 md:grid-cols-2">
              {/* Left Image */}
              <div class="aspect-[3/4] bg-hm-light relative">
                <img 
                  src={selectedProduct.image_url} 
                  alt={selectedProduct.name} 
                  class="object-cover w-full h-full"
                />
              </div>

              {/* Right content info */}
              <div class="p-8 flex flex-col justify-between space-y-4">
                <div class="space-y-2">
                  <span class="text-[10px] text-hm-gray uppercase tracking-widest font-bold">
                    {selectedProduct.category_name}
                  </span>
                  <h2 class="text-lg font-bold text-hm-dark leading-tight">{selectedProduct.name}</h2>
                  <p class="text-base font-extrabold text-hm-red">{formatPrice(selectedProduct.price)}</p>
                  
                  <div class="border-t border-hm-border my-4 pt-4">
                    <span class="text-xs font-semibold text-hm-dark block mb-2">Description</span>
                    <p class="text-xs text-hm-gray leading-relaxed">{selectedProduct.description}</p>
                  </div>

                  <div class="space-y-2">
                    <span class="text-xs font-semibold text-hm-dark block">Choose Size</span>
                    <div class="flex space-x-2 text-xs">
                      {['S', 'M', 'L', 'XL'].map(size => (
                        <button key={size} class="border border-hm-border px-3 py-1.5 hover:border-hm-dark transition-colors font-bold rounded">
                          {size}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div class="space-y-3">
                  <div class="text-xs">
                    {selectedProduct.stock > 0 ? (
                      <span class="text-green-600 font-bold">In Stock: {selectedProduct.stock} items available</span>
                    ) : (
                      <span class="text-hm-red font-bold">Out of Stock</span>
                    )}
                  </div>

                  <button 
                    onClick={() => { addToCart(selectedProduct); setSelectedProduct(null); }}
                    disabled={selectedProduct.stock === 0}
                    class={`w-full text-xs font-bold tracking-wider py-3 uppercase transition-colors rounded ${
                      selectedProduct.stock === 0 
                        ? 'bg-hm-border text-hm-gray cursor-not-allowed'
                        : 'bg-hm-dark text-white hover:bg-hm-red'
                    }`}
                  >
                    Add to shopping bag
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. SHOPPING CART DRAWER */}
      {isCartOpen && (
        <div class="fixed inset-0 z-50 overflow-hidden bg-black bg-opacity-40 flex justify-end">
          <div class="w-full max-w-md bg-white h-full flex flex-col justify-between shadow-2xl animate-slide-in-right border-l border-hm-border">
            
            {/* Cart Header */}
            <div class="px-6 py-5 border-b border-hm-border flex justify-between items-center">
              <div class="flex items-center space-x-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5.5 h-5.5 text-hm-dark">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 1 0-7.5 0v4.5m11.356-1.993 1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 0 1-1.12-1.243l1.264-12A1.125 1.125 0 0 1 5.513 7.5h12.974c.576 0 1.059.435 1.119 1.007ZM8.625 10.5a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm7.5 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                </svg>
                <h2 class="text-sm font-bold text-hm-dark uppercase tracking-wider">Shopping Bag ({totalCartItems})</h2>
              </div>
              <button 
                onClick={() => setIsCartOpen(false)}
                class="text-hm-gray hover:text-hm-dark p-1"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Cart Items List */}
            <div class="flex-grow overflow-y-auto p-6 divide-y divide-hm-border">
              {cart.map((item) => (
                <div key={item.product_id} class="py-4 flex space-x-4 first:pt-0">
                  <div class="w-20 aspect-[3/4] bg-hm-light rounded overflow-hidden flex-shrink-0">
                    <img src={item.image_url} alt={item.name} class="object-cover w-full h-full" />
                  </div>
                  <div class="flex-grow flex flex-col justify-between py-1">
                    <div>
                      <h4 class="text-xs font-bold text-hm-dark line-clamp-1">{item.name}</h4>
                      <p class="text-[10px] text-hm-gray uppercase mt-0.5">{item.category_name}</p>
                    </div>
                    
                    <div class="flex items-center justify-between">
                      {/* Quantity Controls */}
                      <div class="flex items-center border border-hm-border rounded">
                        <button 
                          onClick={() => updateCartQuantity(item.product_id, -1)}
                          class="px-2 py-0.5 hover:bg-hm-light text-xs"
                        >
                          -
                        </button>
                        <span class="px-2 text-xs font-semibold">{item.quantity}</span>
                        <button 
                          onClick={() => updateCartQuantity(item.product_id, 1)}
                          class="px-2 py-0.5 hover:bg-hm-light text-xs"
                        >
                          +
                        </button>
                      </div>

                      <span class="text-xs font-extrabold text-hm-dark">
                        {formatPrice(item.price * item.quantity)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
              {cart.length === 0 && (
                <div class="text-center py-20 text-hm-gray space-y-3">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 mx-auto opacity-40">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 1 0-7.5 0v4.5m11.356-1.993 1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 0 1-1.12-1.243l1.264-12A1.125 1.125 0 0 1 5.513 7.5h12.974c.576 0 1.059.435 1.119 1.007ZM8.625 10.5a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm7.5 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                  </svg>
                  <p class="text-xs">Your shopping bag is empty.</p>
                </div>
              )}
            </div>

            {/* Cart Footer Summary */}
            <div class="p-6 border-t border-hm-border bg-hm-light space-y-4">
              <div class="flex justify-between text-xs font-semibold text-hm-gray">
                <span>Subtotal</span>
                <span class="text-hm-dark font-extrabold text-sm">
                  {formatPrice(cart.reduce((sum, item) => sum + (item.price * item.quantity), 0))}
                </span>
              </div>
              <p class="text-[10px] text-hm-gray leading-tight">
                Shipping and taxes calculated at checkout. Free shipping applies to orders above 1,000,000 VND.
              </p>
              
              <button 
                onClick={handleCheckout}
                disabled={cart.length === 0}
                class={`w-full text-xs font-bold tracking-wider py-3.5 uppercase transition-colors rounded ${
                  cart.length === 0 
                    ? 'bg-hm-border text-hm-gray cursor-not-allowed'
                    : 'bg-hm-red hover:bg-red-700 text-white'
                }`}
              >
                Proceed to checkout
              </button>
            </div>

          </div>
        </div>
      )}

      {/* 6. LOGIN SIGN-IN DIALOG */}
      {isLoginOpen && (
        <div class="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4 bg-black bg-opacity-50 animate-fade-in">
          <div class="bg-white rounded max-w-sm w-full p-8 shadow-2xl relative border border-hm-border animate-slide-up">
            <button 
              onClick={() => { setIsLoginOpen(false); setAuthError(''); }}
              class="absolute top-4 right-4 text-hm-gray hover:text-hm-dark p-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>

            <div class="text-center space-y-2 mb-6">
              <h2 class="text-2xl font-bold tracking-tight text-hm-dark font-serif">Sign In</h2>
              <p class="text-xs text-hm-gray">Access your H&amp;M account and order history.</p>
            </div>

            <form onSubmit={handleLogin} class="space-y-4">
              <div>
                <label class="block text-[10px] font-bold text-hm-dark uppercase mb-1">Username</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. customer01 or admin"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, username: e.target.value }))}
                  class="w-full px-3 py-2 text-xs border border-hm-border focus:border-hm-dark outline-none rounded"
                />
              </div>

              <div>
                <label class="block text-[10px] font-bold text-hm-dark uppercase mb-1">Password</label>
                <input 
                  type="password" 
                  required
                  placeholder="e.g. 123@"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                  class="w-full px-3 py-2 text-xs border border-hm-border focus:border-hm-dark outline-none rounded"
                />
              </div>

              {authError && (
                <p class="text-[11px] text-hm-red font-semibold">{authError}</p>
              )}

              <button 
                type="submit" 
                class="w-full bg-hm-dark hover:bg-hm-red text-white text-xs font-bold py-3 uppercase tracking-wider transition-colors rounded"
              >
                Sign In
              </button>
            </form>

            <div class="border-t border-hm-border mt-6 pt-4 text-center">
              <span class="text-[10px] text-hm-gray block">Demonstration Credentials:</span>
              <span class="text-[10px] font-mono text-hm-dark block mt-1">Admin: <b>admin</b> / <b>123@</b></span>
              <span class="text-[10px] font-mono text-hm-dark block">Customer: <b>customer01</b> / <b>123@</b></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
