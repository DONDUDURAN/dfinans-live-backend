import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Image,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useWardrobeStore } from '../store/wardrobeStore';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import {
  ClothingCategory,
  ClothingItem,
  Color,
  Occasion,
  RootStackParamList,
  Season,
} from '../types';

type Nav = StackNavigationProp<RootStackParamList>;

const CATEGORIES: ClothingCategory[] = ['Tops', 'Bottoms', 'Dresses', 'Outerwear', 'Shoes', 'Accessories', 'Activewear'];
const COLORS: Color[] = ['Black', 'White', 'Gray', 'Beige', 'Brown', 'Navy', 'Blue', 'Green', 'Red', 'Pink', 'Purple', 'Yellow', 'Orange', 'Multi'];
const SEASONS: Season[] = ['Spring', 'Summer', 'Fall', 'Winter', 'All Season'];
const OCCASIONS: Occasion[] = ['Casual', 'Work', 'Formal', 'Sport', 'Party', 'Date Night', 'Beach'];

const COLOR_HEX: Record<Color, string> = {
  Black: '#0D0D0D', White: '#F5F5F0', Gray: '#9E9E9E', Beige: '#C8B89A',
  Brown: '#8B6347', Navy: '#1B2A4A', Blue: '#4A7EC2', Green: '#4CAF7D',
  Red: '#E85555', Pink: '#E87BA0', Purple: '#9B7BE8', Yellow: '#E8C97A',
  Orange: '#E8924C', Multi: '#C9A84C',
};

export const AddItemScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const addItem = useWardrobeStore((s) => s.addItem);

  const [imageUri, setImageUri] = useState<string | null>(null);
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
      Alert.alert('Permission required', 'Camera access is needed to photograph your clothing.');
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

  const toggleSeason = (s: Season) => {
    setSeasons((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);
  };

  const toggleOccasion = (o: Occasion) => {
    setOccasions((prev) => prev.includes(o) ? prev.filter((x) => x !== o) : [...prev, o]);
  };

  const canProceed = () => {
    if (step === 1) return !!imageUri;
    if (step === 2) return !!name && !!category;
    if (step === 3) return !!color && seasons.length > 0;
    return occasions.length > 0;
  };

  const handleSave = () => {
    if (!name || !category || !color || seasons.length === 0 || occasions.length === 0) {
      Alert.alert('Incomplete', 'Please fill in all required fields.');
      return;
    }

    const item: ClothingItem = {
      id: `c_${Date.now()}`,
      name,
      brand: brand || undefined,
      category: category!,
      color: color!,
      season: seasons,
      occasions,
      imageUri: imageUri ?? 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400',
      emoji: '✨',
      tags: [category!.toLowerCase(), color!.toLowerCase()],
      dateAdded: new Date().toISOString().split('T')[0],
      timesWorn: 0,
      isFavorite: false,
    };

    addItem(item);
    navigation.goBack();
    Alert.alert('✨ Added!', `"${name}" has been added to your wardrobe.`);
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={22} color={Colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Add Item</Text>
        <View style={styles.steps}>
          {[1, 2, 3, 4].map((s) => (
            <View
              key={s}
              style={[styles.step, step >= s && styles.stepActive, step === s && styles.stepCurrent]}
            />
          ))}
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Step 1: Photo */}
        {step === 1 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Add a Photo</Text>
            <Text style={styles.stepSubtitle}>Photograph or upload your clothing item</Text>

            <TouchableOpacity
              style={[styles.photoArea, imageUri ? styles.photoAreaFilled : null]}
              onPress={pickImage}
            >
              {imageUri ? (
                <Image source={{ uri: imageUri }} style={styles.photo} resizeMode="cover" />
              ) : (
                <View style={styles.photoPlaceholder}>
                  <Ionicons name="image-outline" size={48} color={Colors.textMuted} />
                  <Text style={styles.photoPlaceholderText}>Tap to select a photo</Text>
                </View>
              )}
            </TouchableOpacity>

            <View style={styles.photoActions}>
              <TouchableOpacity style={[styles.photoBtn, Shadow.sm]} onPress={pickImage}>
                <Ionicons name="images-outline" size={20} color={Colors.textPrimary} />
                <Text style={styles.photoBtnText}>Gallery</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.photoBtn, Shadow.sm]} onPress={takePhoto}>
                <Ionicons name="camera-outline" size={20} color={Colors.textPrimary} />
                <Text style={styles.photoBtnText}>Camera</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Step 2: Details */}
        {step === 2 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Item Details</Text>
            <Text style={styles.stepSubtitle}>Name and categorize your item</Text>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Item Name *</Text>
              <View style={styles.inputRow}>
                <Ionicons name="create-outline" size={18} color={Colors.textMuted} />
                <Text
                  style={[styles.input, !name && styles.inputPlaceholder]}
                  onPress={() => Alert.prompt?.('Item Name', '', (text) => setName(text), 'plain-text', name)}
                >
                  {name || 'e.g. Slim Fit Blazer'}
                </Text>
              </View>
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Brand (optional)</Text>
              <View style={styles.inputRow}>
                <Ionicons name="pricetag-outline" size={18} color={Colors.textMuted} />
                <Text
                  style={[styles.input, !brand && styles.inputPlaceholder]}
                  onPress={() => Alert.prompt?.('Brand', '', (text) => setBrand(text), 'plain-text', brand)}
                >
                  {brand || 'e.g. Zara, Arket, COS'}
                </Text>
              </View>
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Category *</Text>
              <View style={styles.optionGrid}>
                {CATEGORIES.map((cat) => (
                  <TouchableOpacity
                    key={cat}
                    style={[styles.option, category === cat && styles.optionActive]}
                    onPress={() => setCategory(cat)}
                  >
                    <Text style={[styles.optionText, category === cat && styles.optionTextActive]}>
                      {cat}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        )}

        {/* Step 3: Color & Season */}
        {step === 3 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Color & Season</Text>
            <Text style={styles.stepSubtitle}>When and how will you wear this?</Text>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Primary Color *</Text>
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
                    {color === c && (
                      <Ionicons
                        name="checkmark"
                        size={16}
                        color={c === 'White' || c === 'Yellow' ? Colors.background : Colors.textPrimary}
                      />
                    )}
                  </TouchableOpacity>
                ))}
              </View>
              {color && <Text style={styles.colorLabel}>{color}</Text>}
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Season *</Text>
              <View style={styles.optionRow}>
                {SEASONS.map((s) => (
                  <TouchableOpacity
                    key={s}
                    style={[styles.option, seasons.includes(s) && styles.optionActive]}
                    onPress={() => toggleSeason(s)}
                  >
                    <Text style={[styles.optionText, seasons.includes(s) && styles.optionTextActive]}>
                      {s}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        )}

        {/* Step 4: Occasions */}
        {step === 4 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Occasions</Text>
            <Text style={styles.stepSubtitle}>When do you wear this item?</Text>

            <View style={styles.optionGrid}>
              {OCCASIONS.map((occ) => (
                <TouchableOpacity
                  key={occ}
                  style={[styles.option, occasions.includes(occ) && styles.optionActive]}
                  onPress={() => toggleOccasion(occ)}
                >
                  <Text style={[styles.optionText, occasions.includes(occ) && styles.optionTextActive]}>
                    {occ}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Preview */}
            {imageUri && (
              <View style={[styles.preview, Shadow.sm]}>
                <Image source={{ uri: imageUri }} style={styles.previewImage} resizeMode="cover" />
                <View style={styles.previewInfo}>
                  <Text style={styles.previewName}>{name}</Text>
                  {brand && <Text style={styles.previewBrand}>{brand}</Text>}
                  <Text style={styles.previewMeta}>{category} · {color}</Text>
                </View>
              </View>
            )}
          </View>
        )}
      </ScrollView>

      {/* Navigation */}
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
          <Text style={styles.nextBtnText}>
            {step === 4 ? 'Add to Wardrobe' : 'Continue'}
          </Text>
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
    paddingTop: Spacing.base,
    paddingBottom: Spacing.md,
  },
  backBtn: {
    width: 38, height: 38, borderRadius: Radius.md,
    backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.border,
    alignItems: 'center', justifyContent: 'center',
  },
  title: { fontSize: Typography.lg, fontWeight: '800', color: Colors.textPrimary },
  steps: { flexDirection: 'row', gap: 4 },
  step: {
    width: 20, height: 4, borderRadius: 2, backgroundColor: Colors.border,
  },
  stepActive: { backgroundColor: Colors.gold + '66' },
  stepCurrent: { backgroundColor: Colors.gold },
  scroll: { flex: 1 },
  content: { padding: Spacing.base, paddingBottom: Spacing['4xl'] },
  stepContent: { gap: Spacing.xl },
  stepTitle: { fontSize: Typography['2xl'], fontWeight: '800', color: Colors.textPrimary, letterSpacing: -0.5 },
  stepSubtitle: { fontSize: Typography.base, color: Colors.textSecondary, marginTop: -Spacing.md },
  photoArea: {
    height: 280, borderRadius: Radius.xl, overflow: 'hidden',
    backgroundColor: Colors.surface, borderWidth: 2, borderColor: Colors.border, borderStyle: 'dashed',
  },
  photoAreaFilled: { borderStyle: 'solid', borderColor: Colors.gold },
  photo: { width: '100%', height: '100%' },
  photoPlaceholder: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  photoPlaceholderText: { fontSize: Typography.base, color: Colors.textMuted },
  photoActions: { flexDirection: 'row', gap: Spacing.md },
  photoBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 8, backgroundColor: Colors.surface, borderRadius: Radius.lg,
    padding: Spacing.base, borderWidth: 1, borderColor: Colors.border,
  },
  photoBtnText: { fontSize: Typography.base, fontWeight: '600', color: Colors.textPrimary },
  formGroup: { gap: Spacing.md },
  label: { fontSize: Typography.sm, fontWeight: '700', color: Colors.textSecondary, textTransform: 'uppercase', letterSpacing: 0.5 },
  inputRow: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.md,
    backgroundColor: Colors.surface, borderRadius: Radius.lg,
    borderWidth: 1, borderColor: Colors.border, padding: Spacing.base,
  },
  input: { flex: 1, fontSize: Typography.base, color: Colors.textPrimary },
  inputPlaceholder: { color: Colors.textMuted },
  optionGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  optionRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  option: {
    paddingHorizontal: Spacing.base, paddingVertical: 9,
    borderRadius: Radius.full, backgroundColor: Colors.surface,
    borderWidth: 1, borderColor: Colors.border,
  },
  optionActive: { backgroundColor: Colors.gold + '22', borderColor: Colors.gold },
  optionText: { fontSize: Typography.sm, color: Colors.textSecondary, fontWeight: '600' },
  optionTextActive: { color: Colors.gold },
  colorGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  colorSwatch: {
    width: 40, height: 40, borderRadius: Radius.sm,
    borderWidth: 2, borderColor: Colors.border, alignItems: 'center', justifyContent: 'center',
  },
  colorSwatchActive: { borderColor: Colors.gold, borderWidth: 3 },
  colorSwatchLight: { borderColor: Colors.borderLight },
  colorLabel: { fontSize: Typography.sm, color: Colors.textSecondary },
  preview: {
    flexDirection: 'row', gap: Spacing.md, backgroundColor: Colors.surface,
    borderRadius: Radius.lg, padding: Spacing.md, borderWidth: 1, borderColor: Colors.border,
  },
  previewImage: { width: 60, height: 72, borderRadius: Radius.sm, overflow: 'hidden' },
  previewInfo: { flex: 1, gap: 3, justifyContent: 'center' },
  previewName: { fontSize: Typography.base, fontWeight: '700', color: Colors.textPrimary },
  previewBrand: { fontSize: Typography.xs, color: Colors.gold },
  previewMeta: { fontSize: Typography.xs, color: Colors.textSecondary },
  navRow: {
    flexDirection: 'row', gap: Spacing.md,
    padding: Spacing.base, paddingBottom: Spacing.xl,
    borderTopWidth: 1, borderTopColor: Colors.border,
    backgroundColor: Colors.background,
  },
  prevBtn: {
    width: 50, height: 50, borderRadius: Radius.lg, backgroundColor: Colors.surface,
    borderWidth: 1, borderColor: Colors.border, alignItems: 'center', justifyContent: 'center',
  },
  nextBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 8, backgroundColor: Colors.gold, borderRadius: Radius.lg,
    paddingVertical: Spacing.base,
  },
  nextBtnDisabled: { opacity: 0.4 },
  nextBtnText: { fontSize: Typography.base, fontWeight: '800', color: Colors.background },
});
