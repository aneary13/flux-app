export const colors = {
    // Core UI
    background: '#F6F5F2', // Warm off-white
    surface: '#FFFFFF',    // Pure white for cards
    
    // Typography
    textPrimary: '#222222', // Soft charcoal
    textMuted: '#8E8E93',   // Medium grey
    
    // Actions
    actionPrimary: '#2A2A2A', // Dark charcoal for primary buttons
    
    // Biological States (Dynamic)
    stateGreen: '#8FA58A',  // Sage (Performance)
    stateOrange: '#D4A373', // Earthy sand (Caution/Transition)
    stateRed: '#CD7B7B',    // Dusty rose (Recovery)
    
    // Utilities
    borderLight: '#E5E5EA', // Subtle dividers
    transparentBlack: 'rgba(0, 0, 0, 0.03)', // Very subtle shadow base
  };
  
  export const spacing = {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 20, // Standard card internal padding
    xl: 24, // Generous breathing room
    xxl: 32,
    xxxl: 48,
  };
  
  export const radii = {
    sm: 8,
    md: 16, // Minimum for cards
    lg: 20, // Alternative card radius
    button: 24, // Standard button radius
    pill: 999, // Interactive pills
  };
  
  export const shadows = {
    card: {
      shadowColor: colors.textPrimary,
      shadowOffset: { width: 0, height: 4 }, // Subtle vertical lift
      shadowOpacity: 0.03, // Very low opacity
      shadowRadius: 8,
      elevation: 2, // Android equivalent
    },
  };
  
  export const theme = {
    colors,
    spacing,
    radii,
    shadows,
  };
  
  export type Theme = typeof theme;
