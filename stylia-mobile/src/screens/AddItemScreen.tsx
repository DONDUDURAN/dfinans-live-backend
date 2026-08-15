import React, { useState } from 'react';
import {
  Alert,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { StackNavigationProp } from '@react-navigation/stack';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useWardrobeStore } from '../store/wardrobeStore';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { ClothingCategory, ClothingItem, Color, Occasion, RootStackParamList, Season } from '../types';
import { useUserStore } from '../store/userStore';
import { trCategory } from '../utils/translations';

type Nav = StackNavigationProp<RootStackParamList>;

const CATEGORIES: ClothingCategory[] = ['Tops', 'Bottoms', 'Dresses', 'Outerwear', 'Shoes', 'Accessories', 'Activewear'];
const COLORS: Color[] = ['Black', 'White', 'Gray', 'Beige', 'Brown', 'Navy', 'Blue', 'Green', 'Red', 'Pink', 'Purple', 'Yellow', 'Orange', 'Multi'];
const SEASONS: Season[] = ['Spring', 'Summer', 'Fall', 'Winter', 'All Season'];
const OCCASIONS: Occasion[] = ['Casual', 'Work', 'Formal', 'Sport', 'Party', 'Date Night', 'Beach'];

const OCCASION_LABELS: Record<Occasion, string> = {
  Casual: 'Günlük',
  Work: 'Ofis',
  Formal: 'Resmi',
  Sport: 'Spor',
  Party: 'Parti',
  'Date Night': 'Akşam',
  Beach: 'Plaj',
};

const COLOR_HEX: Record<Color, string> = {
  Black: '#0D0D0D',
  White: '#F5F5F0',
  Gray: '#9E9E9E',
  Beige: '#C8B89A',
  Brown: '#8B6347',
  Navy: '#1B2A4A',
  Blue: '#4A7EC2',
  Green: '#4CAF7D',
  Red: '#E85555',
  Pink: '#E87BA0',
  Purple: '#9B7BE8',
  Yellow: '#E8C97A',
  Orange: '#E8924C',
  Multi: '#C9A84C',
};

export const AddItemScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const addItem = useWardrobeStore((s) => s.addItem);
  const setProductLink = useUserStore((s) => s.setProductLink);

  const [imageUri, setImageUri] = useState<string | null>(null);
  const [productLink, setLocalProductLink] = useState('');
  const [name, setName] = useState('');
  const [brand, setBrand] = useState('');
  const [category, setCategory] = useState<ClothingCategory | null>(null);
  const [color, setColor] = useState<Color | null>(null);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [occasions, setOccasions] = useState<Occasion[]>([]);
  const [step, setStep] = useState(1);

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });
    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
    }
  };

  const takePhoto = async () => {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('İzin gerekli', 'Kamera izni olmadan çekim yapılamaz.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });
    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
    }
  };

  const saveProductLink = () => {
    if (!productLink.trim()) {
      Alert.alert('Bağlantı eksik', 'Lütfen ürün bağlantısını girin.');
      return;
    }
    if (!productLink.trim().startsWith('http')) {
      Alert.alert('Geçersiz bağlantı', 'Bağlantı http/https ile başlamalı.');
      return;
    }
    setProductLink(productLink);
    Alert.alert('Kaydedildi', 'Ürün bağlantısı kabin akışına eklendi.');
  };

  const toggleSeason = (s: Season) => {
    setSeasons((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  };

  const toggleOccasion = (o: Occasion) => {
    setOccasions((prev) => (prev.includes(o) ? prev.filter((x) => x !== o) : [...prev, o]));
  };

  const canProceed = () => {
    if (step === 1) return !!imageUri || productLink.trim().length > 0;
    if (step === 2) return !!name.trim() && !!category;
    if (step === 3) return !!color && seasons.length > 0;
    return occasions.length > 0;
  };

  const handleSave = () => {
    if (!name || !category || !color || seasons.length === 0 || occasions.length === 0) {
      Alert.alert('Eksik bilgi', 'Lütfen tüm zorunlu alanları doldurun.');
      return;
    }

    const item: ClothingItem = {
      id: `c_${Date.now()}`,
      name: name.trim(),
      brand: brand.trim() || undefined,
      category,
      color,
      season: seasons,
      occasions,
      imageUri: imageUri ?? 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400',
      emoji: '✨',
      tags: [category.toLowerCase(), color.toLowerCase()],
      dateAdded: new Date().toISOString().split('T')[0],
      timesWorn: 0,
      isFavorite: false,
    };

    addItem(item);
    if (productLink.trim()) {
      setProductLink(productLink);
    }
    navigation.goBack();
    Alert.alert('Parça eklendi', `"${name}" gardırobuna kaydedildi.`);
  };

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + Spacing.base }]}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color={Colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Parça Ekle</Text>
        <View style={styles.steps}>
          {[1, 2, 3, 4].map((s) => (
            <View key={s} style={[styles.step, step >= s && styles.stepActive, step === s && styles.stepCurrent]} />
          ))}
        </View>
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {step === 1 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Kaynak seçimi</Text>
            <Text style={styles.stepSubtitle}>Ürünü kamera, galeri veya ürün linki ile ekleyin.</Text>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Ürün bağlantısı (opsiyonel)</Text>
              <TextInput
                value={productLink}
                onChangeText={setLocalProductLink}
                placeholder="https://marka.com/urun"
                placeholderTextColor={Colors.textMuted}
                autoCapitalize="none"
                style={styles.textInput}
              />
              <TouchableOpacity style={styles.secondaryButton} onPress={saveProductLink}>
                <Text style={styles.secondaryButtonText}>Linki kaydet</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity style={[styles.photoArea, imageUri ? styles.photoAreaFilled : null]} onPress={pickImage}>
              {imageUri ? (
                <Image source={{ uri: imageUri }} style={styles.photo} resizeMode="cover" />
              ) : (
                <View style={styles.photoPlaceholder}>
                  <Ionicons name="image-outline" size={48} color={Colors.textMuted} />
                  <Text style={styles.photoPlaceholderText}>Görsel seçmek için dokunun</Text>
                </View>
              )}
            </TouchableOpacity>

            <View style={styles.photoActions}>
              <TouchableOpacity style={[styles.photoBtn, Shadow.sm]} onPress={pickImage}>
                <Ionicons name="images-outline" size={20} color={Colors.textPrimary} />
                <Text style={styles.photoBtnText}>Galeri</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.photoBtn, Shadow.sm]} onPress={takePhoto}>
                <Ionicons name="camera-outline" size={20} color={Colors.textPrimary} />
                <Text style={styles.photoBtnText}>Kamera</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {step === 2 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Ürün bilgileri</Text>
            <Text style={styles.stepSubtitle}>Ürünün adını ve kategorisini belirleyin.</Text>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Ürün adı *</Text>
              <TextInput
                value={name}
                onChangeText={setName}
                placeholder="Örn. Siyah oversize blazer"
                placeholderTextColor={Colors.textMuted}
                style={styles.textInput}
              />
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Marka (opsiyonel)</Text>
              <TextInput
                value={brand}
                onChangeText={setBrand}
                placeholder="Örn. Zara / COS"
                placeholderTextColor={Colors.textMuted}
                style={styles.textInput}
              />
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Kategori *</Text>
              <View style={styles.optionGrid}>
                {CATEGORIES.map((cat) => (
                  <TouchableOpacity key={cat} style={[styles.option, category === cat && styles.optionActive]} onPress={() => setCategory(cat)}>
                    <Text style={[styles.optionText, category === cat && styles.optionTextActive]}>{trCategory(cat)}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        )}

        {step === 3 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Renk ve sezon</Text>
            <Text style={styles.stepSubtitle}>Bu parçayı hangi dönemde kullanıyorsunuz?</Text>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Ana renk *</Text>
              <View style={styles.colorGrid}>
                {COLORS.map((c) => (
                  <TouchableOpacity
                    key={c}
                    style={[
                      styles.colorSwatch,
                      { backgroundColor: COLOR_HEX[c] },
                      color === c && styles.colorSwatchActive,
                      c === 'White' && styles.colorSwatchLight,
                    ]}
                    onPress={() => setColor(c)}
                  >
                    {color === c && <Ionicons name="checkmark" size={16} color={c === 'White' || c === 'Yellow' ? Colors.background : Colors.textPrimary} />}
                  </TouchableOpacity>
                ))}
              </View>
              {color && <Text style={styles.colorLabel}>{color}</Text>}
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Sezon *</Text>
              <View style={styles.optionRow}>
                {SEASONS.map((s) => (
                  <TouchableOpacity key={s} style={[styles.option, seasons.includes(s) && styles.optionActive]} onPress={() => toggleSeason(s)}>
                    <Text style={[styles.optionText, seasons.includes(s) && styles.optionTextActive]}>{s}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        )}

        {step === 4 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Kullanım alanı</Text>
            <Text style={styles.stepSubtitle}>Bu parçayı en çok hangi durumlarda giyiyorsunuz?</Text>

            <View style={styles.optionGrid}>
              {OCCASIONS.map((occ) => (
                <TouchableOpacity key={occ} style={[styles.option, occasions.includes(occ) && styles.optionActive]} onPress={() => toggleOccasion(occ)}>
                  <Text style={[styles.optionText, occasions.includes(occ) && styles.optionTextActive]}>{OCCASION_LABELS[occ]}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {imageUri && (
              <View style={[styles.preview, Shadow.sm]}>
                <Image source={{ uri: imageUri }} style={styles.previewImage} resizeMode="cover" />
                <View style={styles.previewInfo}>
                  <Text style={styles.previewName}>{name || 'Yeni parça'}</Text>
                  {brand ? <Text style={styles.previewBrand}>{brand}</Text> : null}
                  <Text style={styles.previewMeta}>{category ? trCategory(category) : '-'} · {color || '-'}</Text>
                </View>
              </View>
            )}
          </View>
        )}
      </ScrollView>

      <View style={styles.navRow}>
        {step > 1 && (
          <TouchableOpacity style={styles.prevBtn} onPress={() => setStep(step - 1)}>
            <Ionicons name="arrow-back" size={20} color={Colors.textSecondary} />
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[styles.nextBtn, !canProceed() && styles.nextBtnDisabled, Shadow.gold]}
          onPress={step === 4 ? handleSave : () => setStep(step + 1)}
          disabled={!canProceed()}
        >
          <Text style={styles.nextBtnText}>{step === 4 ? 'Gardıroba ekle' : 'Devam et'}</Text>
          <Ionicons name={step === 4 ? 'checkmark' : 'arrow-forward'} size={18} color={Colors.background} />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.md,
  },
  backBtn: {
    width: 38,
    height: 38,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { fontSize: Typography.lg, fontWeight: '800', color: Colors.textPrimary },
  steps: { flexDirection: 'row', gap: 4 },
  step: { width: 20, height: 4, borderRadius: 2, backgroundColor: Colors.border },
  stepActive: { backgroundColor: Colors.gold + '66' },
  stepCurrent: { backgroundColor: Colors.gold },
  scroll: { flex: 1 },
  content: { padding: Spacing.base, paddingBottom: Spacing['4xl'] },
  stepContent: { gap: Spacing.xl },
  stepTitle: { fontSize: Typography['2xl'], fontWeight: '800', color: Colors.textPrimary, letterSpacing: -0.5 },
  stepSubtitle: { fontSize: Typography.base, color: Colors.textSecondary, marginTop: -Spacing.md },
  formGroup: { gap: Spacing.sm },
  label: {
    fontSize: Typography.sm,
    fontWeight: '700',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  textInput: {
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    color: Colors.textPrimary,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
    fontSize: Typography.base,
  },
  secondaryButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.md,
    paddingVertical: 7,
    borderRadius: Radius.full,
    borderColor: Colors.gold,
    borderWidth: 1,
    backgroundColor: Colors.gold + '22',
  },
  secondaryButtonText: {
    color: Colors.gold,
    fontWeight: '700',
    fontSize: Typography.xs,
  },
  photoArea: {
    height: 280,
    borderRadius: Radius.xl,
    overflow: 'hidden',
    backgroundColor: Colors.surface,
    borderWidth: 2,
    borderColor: Colors.border,
    borderStyle: 'dashed',
  },
  photoAreaFilled: { borderStyle: 'solid', borderColor: Colors.gold },
  photo: { width: '100%', height: '100%' },
  photoPlaceholder: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  photoPlaceholderText: { fontSize: Typography.base, color: Colors.textMuted },
  photoActions: { flexDirection: 'row', gap: Spacing.md },
  photoBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  photoBtnText: { fontSize: Typography.base, fontWeight: '600', color: Colors.textPrimary },
  optionGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  optionRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  option: {
    paddingHorizontal: Spacing.base,
    paddingVertical: 9,
    borderRadius: Radius.full,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  optionActive: { backgroundColor: Colors.gold + '22', borderColor: Colors.gold },
  optionText: { fontSize: Typography.sm, color: Colors.textSecondary, fontWeight: '600' },
  optionTextActive: { color: Colors.gold },
  colorGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  colorSwatch: {
    width: 40,
    height: 40,
    borderRadius: Radius.sm,
    borderWidth: 2,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  colorSwatchActive: { borderColor: Colors.gold, borderWidth: 3 },
  colorSwatchLight: { borderColor: Colors.borderLight },
  colorLabel: { fontSize: Typography.sm, color: Colors.textSecondary },
  preview: {
    flexDirection: 'row',
    gap: Spacing.md,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  previewImage: { width: 60, height: 72, borderRadius: Radius.sm, overflow: 'hidden' },
  previewInfo: { flex: 1, gap: 3, justifyContent: 'center' },
  previewName: { fontSize: Typography.base, fontWeight: '700', color: Colors.textPrimary },
  previewBrand: { fontSize: Typography.xs, color: Colors.gold },
  previewMeta: { fontSize: Typography.xs, color: Colors.textSecondary },
  navRow: {
    flexDirection: 'row',
    gap: Spacing.md,
    padding: Spacing.base,
    paddingBottom: Spacing.xl,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.background,
  },
  prevBtn: {
    width: 50,
    height: 50,
    borderRadius: Radius.lg,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  nextBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.gold,
    borderRadius: Radius.lg,
    paddingVertical: Spacing.base,
  },
  nextBtnDisabled: { opacity: 0.4 },
  nextBtnText: { fontSize: Typography.base, fontWeight: '800', color: Colors.background },
});
