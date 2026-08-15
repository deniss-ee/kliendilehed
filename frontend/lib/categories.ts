export interface Category {
  id: string;
  name_et: string;
  name_en: string;
  icon: string;
  keywords: string[];
}

export const CATEGORIES: Category[] = [
  {
    id: "all",
    name_et: "Kõik kaubad",
    name_en: "All Items",
    icon: "🛒",
    keywords: [],
  },
  {
    id: "dairy",
    name_et: "Piim, Munad & Või",
    name_en: "Dairy, Eggs & Butter",
    icon: "🥛",
    keywords: ["piim", "või", "hapukoor", "koor", "keefir", "jogurt", "kohupiim", "muna", "juust"],
  },
  {
    id: "coffee",
    name_et: "Kohv, Tee & Kakao",
    name_en: "Coffee & Tea",
    icon: "☕",
    keywords: ["kohv", "kohvioad", "paulig", "lavazza", "tee", "kakao", "nescafe", "löfbergs"],
  },
  {
    id: "bakery",
    name_et: "Leib, Sai & Pagar",
    name_en: "Bakery & Bread",
    icon: "🥖",
    keywords: ["leib", "sai", "sepik", "croissant", "kukkel", "fazer", "leibur", "eesti pagar"],
  },
  {
    id: "meat",
    name_et: "Liha, Kana & Kala",
    name_en: "Meat, Poultry & Fish",
    icon: "🥩",
    keywords: ["liha", "hakkliha", "kana", "filee", "vorst", "sink", "viiner", "kala", "lõhe", "rakvere", "maks & moorits", "nõo"],
  },
  {
    id: "produce",
    name_et: "Puu- & Köögiviljad",
    name_en: "Fruits & Vegetables",
    icon: "🍎",
    keywords: ["õun", "banaan", "tomat", "kurk", "kartul", "porgand", "apelsin", "sibul", "avokaado", "salat"],
  },
  {
    id: "drinks",
    name_et: "Karastusjoogid & Mahlad",
    name_en: "Drinks & Juices",
    icon: "🥤",
    keywords: ["vesi", "mahl", "aura", "coca-cola", "pepsi", "limonaad", "kali", "õlu", "siider", "jook"],
  },
  {
    id: "sweets",
    name_et: "Maiustused & Näksid",
    name_en: "Sweets & Snacks",
    icon: "🍫",
    keywords: ["šokolaad", "kalev", "kommid", "küpsised", "krõpsud", "lays", "pähklid", "jäätis"],
  },
  {
    id: "household",
    name_et: "Kodu & Puhastus",
    name_en: "Household & Cleaning",
    icon: "🧹",
    keywords: ["paber", "pesugeel", "seep", "hambahari", "fairy", "ariel", "persil", "šampoon"],
  },
];
