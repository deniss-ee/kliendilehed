export interface StoreProfile {
  code: string;
  name: string;
  slug: string;
  logoColor: string;
  bannerBg: string;
  slogan: string;
  loyaltyCardName: string;
  loyaltyBenefit: string;
  websiteUrl: string;
  flyerUrl: string;
  storeCount: number;
}

export const STORES: Record<string, StoreProfile> = {
  selver: {
    code: "SELVER",
    name: "Selver",
    slug: "selver",
    logoColor: "#d9251d",
    bannerBg: "from-red-700 via-rose-900 to-slate-950",
    slogan: "Hea mõte igaks päevaks",
    loyaltyCardName: "Partnerkaart",
    loyaltyBenefit: "Partnerkaart gives up to 5% bonus points, special Partnerkaart campaign discounts, and birthday benefits.",
    websiteUrl: "https://www.selver.ee",
    flyerUrl: "https://www.selver.ee/kliendileht",
    storeCount: 74,
  },
  prisma: {
    code: "PRISMA",
    name: "Prisma Peremarket",
    slug: "prisma",
    logoColor: "#00823b",
    bannerBg: "from-emerald-700 via-teal-900 to-slate-950",
    slogan: "Püsivalt soodsad hinnad",
    loyaltyCardName: "Prisma Konto (S-Etukortti)",
    loyaltyBenefit: "Püsivalt soodne guarantee + S-Konto bonus system for maximum monthly household savings.",
    websiteUrl: "https://www.prismamarket.ee",
    flyerUrl: "https://www.prismamarket.ee/kampaaniad",
    storeCount: 14,
  },
  coop: {
    code: "COOP",
    name: "Coop Eesti",
    slug: "coop",
    logoColor: "#004b92",
    bannerBg: "from-blue-700 via-indigo-900 to-slate-950",
    slogan: "Hoiame kokku!",
    loyaltyCardName: "Säästukaart & Säästukaart Pluss",
    loyaltyBenefit: "Säästukaart exclusive member discount prices, bonus points, and Coop Pank extra rebate.",
    websiteUrl: "https://ecoop.ee",
    flyerUrl: "https://www.coop.ee/kliendileht",
    storeCount: 320,
  },
  rimi: {
    code: "RIMI",
    name: "Rimi Baltic",
    slug: "rimi",
    logoColor: "#e30613",
    bannerBg: "from-red-600 via-red-950 to-slate-950",
    slogan: "Iga päev parem",
    loyaltyCardName: "Minu Rimi Kaart",
    loyaltyBenefit: "1% Rimi money back on all purchases, personalized coupons, and Tervisereede fruit discounts.",
    websiteUrl: "https://www.rimi.ee/epood",
    flyerUrl: "https://www.rimi.ee/pakkumised",
    storeCount: 88,
  },
  maxima: {
    code: "MAXIMA",
    name: "Maxima Eesti",
    slug: "maxima",
    logoColor: "#002d72",
    bannerBg: "from-indigo-800 via-blue-950 to-slate-950",
    slogan: "See on sellest, mis oluline",
    loyaltyCardName: "Aitäh Kaart",
    loyaltyBenefit: "1% Maxima money back, Aitäh exclusive weekly club offers, and birthday discounts.",
    websiteUrl: "https://www.barbora.ee",
    flyerUrl: "https://www.maxima.ee/kliendilehed",
    storeCount: 84,
  },
  lidl: {
    code: "LIDL",
    name: "Lidl Eesti",
    slug: "lidl",
    logoColor: "#0050aa",
    bannerBg: "from-sky-700 via-blue-900 to-slate-950",
    slogan: "Lihtsalt soodne",
    loyaltyCardName: "Lidl Plus App",
    loyaltyBenefit: "Lidl Plus digital coupons, scratch & win bonuses, and member-exclusive discount activations.",
    websiteUrl: "https://www.lidl.ee",
    flyerUrl: "https://www.lidl.ee/pakkumised",
    storeCount: 16,
  },
};
