import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { AlertTriangle } from 'lucide-react-native';
import { theme } from '../lib/theme';

const C = theme.arc.dark;

type Props = {
  visible: boolean;
  onRetry?: () => void;
};

// claude-sonnet-4-6
export const OfflineBanner = ({ visible, onRetry }: Props) => {
  const translateY = useRef(new Animated.Value(-50)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const mounted = useRef(false);
  const [rendered, setRendered] = React.useState(visible);

  // claude-sonnet-4-6
  useEffect(() => {
    if (visible) {
      mounted.current = true;
      setRendered(true);
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: 0,
          duration: 180,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 1,
          duration: 180,
          useNativeDriver: true,
        }),
      ]).start();
      return;
    }

    if (mounted.current) {
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: -50,
          duration: 160,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0,
          duration: 160,
          useNativeDriver: true,
        }),
      ]).start(() => {
        mounted.current = false;
        setRendered(false);
      });
    }
  }, [opacity, translateY, visible]);

  if (!rendered) {
    return null;
  }

  return (
    <Animated.View style={[s.wrap, { opacity, transform: [{ translateY }] }]} pointerEvents="box-none">
      <View style={s.banner}>
        <View style={s.left}>
          <AlertTriangle size={14} color="#fef08a" />
          <Text style={s.text}>No internet connection</Text>
        </View>
        {onRetry ? (
          <TouchableOpacity onPress={onRetry} activeOpacity={0.8}>
            <Text style={s.retry}>Retry</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    </Animated.View>
  );
};

const s = StyleSheet.create({
  wrap: {
    paddingHorizontal: 16,
    paddingTop: 10,
    zIndex: 10,
  },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ca8a04',
    backgroundColor: '#1c1505',
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
    paddingRight: 12,
  },
  text: {
    color: '#fef08a',
    fontSize: 12.5,
    fontWeight: '600',
  },
  retry: {
    color: '#fef08a',
    fontSize: 12.5,
    fontWeight: '700',
  },
});
