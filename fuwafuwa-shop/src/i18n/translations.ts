export type Language = 'zh' | 'en';

type CategoryKey = 'all' | 'food' | 'toy' | 'accessory' | 'care' | 'home' | 'favorites';

export interface Translations {
  nav: {
    home: string;
    cart: string;
    title: string;
    stores: string;
    myOrders: string;
    login: string;
  };

  home: {
    shopTitle: string;
    activeDiscounts: string;
  };

  petRoom: {
    interactions: {
      brush: string;
      play: string;
      feed: string;
    };
  };

  product: {
    /** 分類圖示檔名 */
    categories: Record<CategoryKey, string>;
    categoryDescriptions: Record<CategoryKey, string>;
    addToCart: string;
    stock: string;
    outOfStock: string;
    quantity: string;
    description: string;
    back: string;
    store: string;
    eventDiscount: string;
    alsoBought: string;
    notFound: string;
    loading: string;
    pieces: string;
  };

  shop: {
    searchPlaceholder: string;
    search: string;
    allStores: string;
    sortNewest: string;
    sortPriceAsc: string;
    sortPriceDesc: string;
    empty: string;
    loadFailed: string;
    resultCount: string;
  };

  store: {
    title: string;
    products: string;
    reviews: string;
    noReviews: string;
    avgRating: string;
    reviewCount: string;
    productCount: string;
    address: string;
    phone: string;
    email: string;
    viewStore: string;
  };

  cart: {
    title: string;
    empty: string;
    subtotal: string;
    checkout: string;
    remove: string;
    items: string;
    loginFirst: string;
    customerOnly: string;
    eventDiscount: string;
    seasonalDiscount: string;
    tax: string;
    shippingFee: string;
    shippingDiscount: string;
    total: string;
    appliedDiscounts: string;
    continueShopping: string;
  };

  checkout: {
    title: string;
    items: string;
    recipient: string;
    recipientName: string;
    recipientPhone: string;
    recipientAddress: string;
    summary: string;
    pay: string;
    paying: string;
    backToCart: string;
    emptyCart: string;
  };

  orders: {
    title: string;
    orderNo: string;
    orderTime: string;
    total: string;
    itemCount: string;
    details: string;
    empty: string;
    startShopping: string;
    returnStatus: string;
    statTotal: string;
    statActive: string;
    statClosed: string;
    statSpent: string;
    back: string;
  };

  reactions: {
    hungry: string;
    excited: string;
    happy: string;
    curious: string;
    neutral: string;
  };

  messages: {
    addedToCart: string;
    addToCartFailed: string;
    thankYou: string;
  };

  login: {
    title: string;
    subtitle: string;
    registerTitle: string;
    registerSubtitle: string;
    loginid: string;
    loginidPlaceholder: string;
    name: string;
    email: string;
    address: string;
    phone: string;
    password: string;
    passwordPlaceholder: string;
    loginButton: string;
    loggingIn: string;
    registerButton: string;
    registering: string;
    noAccount: string;
    signUp: string;
    haveAccount: string;
    signIn: string;
    backToHome: string;
    demoAccounts: string;
    loginRequired: string;
  };
}

export const translations: Record<Language, Translations> = {
  zh: {
    nav: {
      home: '首頁',
      cart: '購物車',
      title: 'FUWA FUWA 寵物商店',
      stores: '商店',
      myOrders: '我的訂單',
      login: '登入',
    },
    home: {
      shopTitle: '商店',
      activeDiscounts: '本日優惠',
    },
    petRoom: {
      interactions: {
        brush: '梳毛',
        play: '玩耍',
        feed: '餵食',
      },
    },
    product: {
      categories: {
        all: 'All.webp',
        food: 'can.webp',
        toy: 'ball.webp',
        accessory: 'collar.webp',
        care: 'brush.webp',
        home: 'cage.webp',
        favorites: 'dog_heart_press_2.webp',
      },
      categoryDescriptions: {
        all: '所有商品',
        food: '寵物食品',
        toy: '寵物玩具',
        accessory: '寵物配件',
        care: '清潔美容',
        home: '居家用品',
        favorites: '我的最愛',
      },
      addToCart: '加入購物車',
      stock: '庫存',
      outOfStock: '已售完',
      quantity: '數量',
      description: '商品說明',
      back: '← 返回',
      store: '販售商店',
      eventDiscount: '特殊活動',
      alsoBought: '買了這個商品的人也買了',
      notFound: '找不到這個商品',
      loading: '載入中...',
      pieces: '個',
    },
    shop: {
      searchPlaceholder: '搜尋商品名稱或說明…',
      search: '搜尋',
      allStores: '全部商店',
      sortNewest: '最新上架',
      sortPriceAsc: '價格低到高',
      sortPriceDesc: '價格高到低',
      empty: '暫無商品',
      loadFailed: '商品載入失敗',
      resultCount: '件商品',
    },
    store: {
      title: '商店一覽',
      products: '商店商品',
      reviews: '顧客評價',
      noReviews: '目前還沒有評價',
      avgRating: '平均評分',
      reviewCount: '則評價',
      productCount: '件商品',
      address: '地址',
      phone: '電話',
      email: 'Email',
      viewStore: '查看商店',
    },
    cart: {
      title: '購物車',
      empty: '購物車是空的',
      subtotal: '小計',
      checkout: '結帳',
      remove: '刪除',
      items: '件商品',
      loginFirst: '請先登入才能使用購物車',
      customerOnly: '只有顧客帳號可以使用購物車',
      eventDiscount: '特殊活動折扣',
      seasonalDiscount: '季節性折扣',
      tax: '稅',
      shippingFee: '運費',
      shippingDiscount: '運費折扣',
      total: '總額',
      appliedDiscounts: '已套用的折扣',
      continueShopping: '繼續購物',
    },
    checkout: {
      title: '訂單確認',
      items: '訂單商品',
      recipient: '收件資訊',
      recipientName: '收件人姓名',
      recipientPhone: '聯絡電話',
      recipientAddress: '收件地址',
      summary: '金額明細',
      pay: '確認付款',
      paying: '付款中...',
      backToCart: '返回購物車',
      emptyCart: '購物車是空的',
    },
    orders: {
      title: '我的訂單',
      orderNo: '訂單編號',
      orderTime: '訂購時間',
      total: '訂單總額',
      itemCount: '商品數量',
      details: '查看詳情',
      empty: '您還沒有任何訂單',
      startShopping: '開始購物',
      returnStatus: '退貨',
      statTotal: '總訂單數',
      statActive: '進行中',
      statClosed: '已完成',
      statSpent: '總消費金額',
      back: '← 返回我的訂單',
    },
    reactions: {
      hungry: '好餓啊！',
      excited: '好想玩！',
      happy: '好開心！',
      curious: '好好奇！',
      neutral: '真不錯！',
    },
    messages: {
      addedToCart: '已加入購物車！',
      addToCartFailed: '加入購物車失敗，請稍後再試',
      thankYou: '感謝您的購買！',
    },
    login: {
      title: '會員登入',
      subtitle: '歡迎回到 FUWA FUWA 寵物商店',
      registerTitle: '註冊會員',
      registerSubtitle: '加入 FUWA FUWA，開始幫毛孩購物',
      loginid: '帳號',
      loginidPlaceholder: '請輸入帳號',
      name: '姓名',
      email: '電子信箱',
      address: '地址',
      phone: '電話（選填）',
      password: '密碼',
      passwordPlaceholder: '請輸入密碼',
      loginButton: '登入',
      loggingIn: '登入中...',
      registerButton: '註冊並登入',
      registering: '註冊中...',
      noAccount: '還沒有帳號嗎？',
      signUp: '立即註冊',
      haveAccount: '已經有帳號了？',
      signIn: '前往登入',
      backToHome: '← 返回首頁',
      demoAccounts: '示範帳號',
      loginRequired: '請先登入才能加入購物車',
    },
  },
  en: {
    nav: {
      home: 'Home',
      cart: 'Cart',
      title: 'FUWA FUWA Pet Shop',
      stores: 'Stores',
      myOrders: 'My Orders',
      login: 'Login',
    },
    home: {
      shopTitle: 'SHOP',
      activeDiscounts: "Today's deals",
    },
    petRoom: {
      interactions: {
        brush: 'Brush',
        play: 'Play',
        feed: 'Feed',
      },
    },
    product: {
      categories: {
        all: 'All.webp',
        food: 'can.webp',
        toy: 'ball.webp',
        accessory: 'collar.webp',
        care: 'brush.webp',
        home: 'cage.webp',
        favorites: 'dog_heart_press_2.webp',
      },
      categoryDescriptions: {
        all: 'All Products',
        food: 'Pet Food',
        toy: 'Pet Toys',
        accessory: 'Pet Accessories',
        care: 'Grooming & Care',
        home: 'Home & Living',
        favorites: 'My Favorites',
      },
      addToCart: 'Add to Cart',
      stock: 'Stock',
      outOfStock: 'Out of Stock',
      quantity: 'Quantity',
      description: 'Description',
      back: '← Back',
      store: 'Sold by',
      eventDiscount: 'Special event',
      alsoBought: 'Customers who bought this also bought',
      notFound: 'Product not found',
      loading: 'Loading...',
      pieces: ' pcs',
    },
    shop: {
      searchPlaceholder: 'Search products…',
      search: 'Search',
      allStores: 'All stores',
      sortNewest: 'Newest',
      sortPriceAsc: 'Price: low to high',
      sortPriceDesc: 'Price: high to low',
      empty: 'No products',
      loadFailed: 'Failed to load products',
      resultCount: 'products',
    },
    store: {
      title: 'Our Stores',
      products: 'Products',
      reviews: 'Reviews',
      noReviews: 'No reviews yet',
      avgRating: 'Average rating',
      reviewCount: 'reviews',
      productCount: 'products',
      address: 'Address',
      phone: 'Phone',
      email: 'Email',
      viewStore: 'View store',
    },
    cart: {
      title: 'Shopping Cart',
      empty: 'Your cart is empty',
      subtotal: 'Subtotal',
      checkout: 'Checkout',
      remove: 'Remove',
      items: 'items',
      loginFirst: 'Please log in to use the cart',
      customerOnly: 'Only customer accounts can use the cart',
      eventDiscount: 'Special event discount',
      seasonalDiscount: 'Seasonal discount',
      tax: 'Tax',
      shippingFee: 'Shipping',
      shippingDiscount: 'Shipping discount',
      total: 'Total',
      appliedDiscounts: 'Applied discounts',
      continueShopping: 'Continue shopping',
    },
    checkout: {
      title: 'Confirm Order',
      items: 'Items',
      recipient: 'Recipient',
      recipientName: 'Recipient name',
      recipientPhone: 'Phone',
      recipientAddress: 'Address',
      summary: 'Amount',
      pay: 'Confirm payment',
      paying: 'Paying...',
      backToCart: 'Back to cart',
      emptyCart: 'Your cart is empty',
    },
    orders: {
      title: 'My Orders',
      orderNo: 'Order No.',
      orderTime: 'Ordered at',
      total: 'Total',
      itemCount: 'Items',
      details: 'Details',
      empty: "You don't have any orders yet",
      startShopping: 'Start shopping',
      returnStatus: 'Return',
      statTotal: 'Orders',
      statActive: 'In progress',
      statClosed: 'Completed',
      statSpent: 'Total spent',
      back: '← Back to my orders',
    },
    reactions: {
      hungry: "I'm hungry!",
      excited: "Let's play!",
      happy: "I'm happy!",
      curious: "I'm curious!",
      neutral: 'Nice!',
    },
    messages: {
      addedToCart: 'Added to cart!',
      addToCartFailed: 'Failed to add to cart, please try again later',
      thankYou: 'Thank you for your purchase!',
    },
    login: {
      title: 'Member Login',
      subtitle: 'Welcome back to FUWA FUWA Pet Shop',
      registerTitle: 'Sign Up',
      registerSubtitle: 'Join FUWA FUWA and start shopping for your pet',
      loginid: 'Login ID',
      loginidPlaceholder: 'Enter your login ID',
      name: 'Name',
      email: 'Email',
      address: 'Address',
      phone: 'Phone (optional)',
      password: 'Password',
      passwordPlaceholder: 'Enter your password',
      loginButton: 'Login',
      loggingIn: 'Logging in...',
      registerButton: 'Sign up & log in',
      registering: 'Signing up...',
      noAccount: "Don't have an account?",
      signUp: 'Sign up now',
      haveAccount: 'Already have an account?',
      signIn: 'Log in',
      backToHome: '← Back to Home',
      demoAccounts: 'Demo accounts',
      loginRequired: 'Please login to add items to cart',
    },
  },
};
