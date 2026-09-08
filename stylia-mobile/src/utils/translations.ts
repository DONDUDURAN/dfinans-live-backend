const CATEGORY_TR: Record<string, string> = {
  All: 'Tümü',
  Tops: 'Üst',
  Bottoms: 'Alt',
  Shoes: 'Ayakkabı',
  Accessories: 'Aksesuar',
  Outerwear: 'Dış Giyim',
  Dresses: 'Elbise',
  Activewear: 'Spor',
};

const OCCASION_TR: Record<string, string> = {
  Casual: 'Günlük',
  Work: 'Ofis',
  Formal: 'Resmi',
  Sport: 'Spor',
  Party: 'Parti',
  'Date Night': 'Akşam',
  Beach: 'Plaj',
};

export const trCategory = (value: string) => CATEGORY_TR[value] ?? value;
export const trOccasion = (value: string) => OCCASION_TR[value] ?? value;
