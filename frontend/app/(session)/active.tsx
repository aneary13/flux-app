import React, { useState, useRef, useEffect } from 'react';
import { View, StyleSheet, TouchableOpacity, FlatList, useWindowDimensions, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { useSessionStore } from '../../store/useSessionStore';
import { Typography } from '../../components/core/Typography';
import { Card } from '../../components/core/Card';
import { theme } from '../../theme';
import { ChecklistCard } from '../../components/domain/ChecklistCard';
import { ExerciseCard } from '../../components/domain/ExerciseCard';

export default function ActiveSessionScreen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const { sessionData, addBlockTime } = useSessionStore();
  
  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  // --- TIMER REFS ---
  const lastEntryTime = useRef<number>(Date.now());
  const previousIndex = useRef<number>(0);

  // Bulletproof Scroll Tracking & Timer Logging
  const viewabilityConfig = useRef({ viewAreaCoveragePercentThreshold: 50 }).current;
  const onViewableItemsChanged = useRef(({ viewableItems }: any) => {
    if (viewableItems.length > 0) {
      const newIndex = viewableItems[0].index;
      
      if (newIndex !== previousIndex.current) {
        // Fetch the freshest state directly to avoid stale closures
        const state = useSessionStore.getState();
        const blocks = state.sessionData?.blocks;
        
        if (blocks && blocks[previousIndex.current]) {
          const timeSpent = Date.now() - lastEntryTime.current;
          const prevBlockType = blocks[previousIndex.current].type;
          state.addBlockTime(prevBlockType, timeSpent); // Accumulate time
        }
        
        // Reset local clock for the new block
        lastEntryTime.current = Date.now();
        previousIndex.current = newIndex;
        setCurrentIndex(newIndex);
      }
    }
  }).current;

  // On initial mount, ensure the timer is reset
  useEffect(() => {
    lastEntryTime.current = Date.now();
  }, []);

  if (!sessionData) {
    return (
      <View style={styles.center}>
        <Typography>No active session data.</Typography>
      </View>
    );
  }

  const blocks = sessionData.blocks;
  const currentBlock = blocks[currentIndex];
  const isLastBlock = currentIndex === blocks.length - 1;

  // --- Navigation Handlers ---
  const handleNextBlock = () => {
    if (!isLastBlock) {
      flatListRef.current?.scrollToIndex({ index: currentIndex + 1, animated: true });
    } else {
      // Record time for the final block before navigating away
      const timeSpent = Date.now() - lastEntryTime.current;
      addBlockTime(currentBlock.type, timeSpent);
      router.push('/(session)/complete');
    }
  };

  const handlePrevBlock = () => {
    if (currentIndex > 0) {
      flatListRef.current?.scrollToIndex({ index: currentIndex - 1, animated: true });
    }
  };

  const renderBlockSlide = ({ item }: { item: typeof blocks[0] }) => {
    const checklistExercises = item.exercises.filter(ex => ex.tracking_unit === 'CHECKLIST');
    const standardExercises = item.exercises.filter(ex => ex.tracking_unit !== 'CHECKLIST');

    return (
      <View style={[styles.slideContainer, { width }]}>
        <Card style={styles.blockCard} padding={0}>
          <ScrollView 
            contentContainerStyle={styles.cardScrollContent} 
            showsVerticalScrollIndicator={false}
            // Allow touches to pass through to the submit button
            keyboardShouldPersistTaps="handled" 
          >
            <Typography variant="h2" style={{ marginBottom: theme.spacing.md }}>
              {item.label}
            </Typography>
            
            {checklistExercises.length > 0 && (
              <ChecklistCard 
                exercises={checklistExercises} 
                title={item.type === 'PREP' ? 'Mobility & Prep' : item.type === 'POWER' ? 'Plyometrics' : undefined}
              />
            )}

            {standardExercises.length > 0 && (
              <View style={{ gap: theme.spacing.md, marginTop: checklistExercises.length > 0 ? theme.spacing.md : 0 }}>
                {standardExercises.map((ex, exIndex) => (
                  <ExerciseCard key={ex.id || `ex-${exIndex}`} exercise={ex} />
                ))}
              </View>
            )}
          </ScrollView>
        </Card>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={28} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <View style={styles.blockPill}>
            <Typography variant="label" style={styles.blockPillText}>{currentBlock?.type || '...'}</Typography>
          </View>
        </View>
        <Typography variant="body" style={styles.pageIndicator}>{currentIndex + 1} / {blocks.length}</Typography>
      </View>

      {/* Horizontal Pager */}
      <FlatList
        ref={flatListRef}
        data={blocks}
        keyExtractor={(item, index) => item.id || `block-${index}`}
        renderItem={renderBlockSlide}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        bounces={false}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
      />

      {/* Footer Actions */}
      <View style={styles.footer}>
        <View style={styles.footerRow}>
          {currentIndex > 0 ? (
            <TouchableOpacity style={styles.iconButton} onPress={handlePrevBlock} activeOpacity={0.7}>
              <Ionicons name="arrow-back" size={24} color={theme.colors.textPrimary} />
            </TouchableOpacity>
          ) : (
            <View style={styles.iconButtonPlaceholder} />
          )}
          <TouchableOpacity style={styles.nextButton} onPress={handleNextBlock} activeOpacity={0.8}>
            <Typography style={styles.nextButtonText}>{isLastBlock ? "Finish Session" : "Next Block"}</Typography>
            {!isLastBlock && <Ionicons name="arrow-forward" size={20} color={theme.colors.surface} style={styles.nextIcon} />}
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

// ... Keep existing styles ...
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background, paddingTop: 60 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: theme.spacing.xl, marginBottom: theme.spacing.md },
  backButton: { padding: theme.spacing.xs, marginLeft: -theme.spacing.xs },
  headerCenter: { flex: 1, alignItems: 'center' },
  blockPill: { backgroundColor: theme.colors.actionPrimary, paddingVertical: 6, paddingHorizontal: 16, borderRadius: theme.radii.pill },
  blockPillText: { color: theme.colors.surface, fontWeight: 'bold', letterSpacing: 1 },
  pageIndicator: { color: theme.colors.textMuted, width: 40, textAlign: 'right' },
  slideContainer: { flex: 1, paddingHorizontal: theme.spacing.xl, paddingBottom: theme.spacing.md },
  blockCard: { flex: 1, overflow: 'hidden' },
  cardScrollContent: { padding: theme.spacing.xl, flexGrow: 1 },
  footer: { paddingHorizontal: theme.spacing.xl, paddingBottom: 40, paddingTop: theme.spacing.md, backgroundColor: theme.colors.background },
  footerRow: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.md },
  iconButton: { width: 56, height: 56, borderRadius: 28, borderWidth: 1, borderColor: theme.colors.borderLight, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.surface },
  iconButtonPlaceholder: { width: 56, height: 56 },
  nextButton: { flex: 1, height: 56, backgroundColor: theme.colors.actionPrimary, borderRadius: theme.radii.button, flexDirection: 'row', justifyContent: 'center', alignItems: 'center' },
  nextButtonText: { color: theme.colors.surface, fontSize: 16, fontWeight: '600' },
  nextIcon: { marginLeft: theme.spacing.sm }
});
