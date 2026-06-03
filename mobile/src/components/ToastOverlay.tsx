import React, { useEffect, useRef, useState } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';
import { CheckCircle2, CircleAlert, Info } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { Toast, useToastStore } from '../lib/toast';

const C = theme.arc.dark;

type ToastAnimation = {
  opacity: Animated.Value;
  translateY: Animated.Value;
};

// claude-sonnet-4-6
function getToastColors(type: Toast['type']): { borderColor: string; Icon: React.ComponentType<any> } {
  if (type === 'success') return { borderColor: theme.arc.accent, Icon: CheckCircle2 };
  if (type === 'error') return { borderColor: '#ef4444', Icon: CircleAlert };
  return { borderColor: C.line, Icon: Info };
}

// claude-sonnet-4-6
function createToastAnimation(): ToastAnimation {
  return {
    opacity: new Animated.Value(0),
    translateY: new Animated.Value(16),
  };
}

// claude-sonnet-4-6
export const ToastOverlay = () => {
  const toasts = useToastStore((state) => state.toasts);
  const [renderedToasts, setRenderedToasts] = useState<Toast[]>([]);
  const animationsRef = useRef<Record<string, ToastAnimation>>({});

  // claude-sonnet-4-6
  useEffect(() => {
    const nextIds = new Set(toasts.map((toast) => toast.id));

    toasts.forEach((toast) => {
      if (!animationsRef.current[toast.id]) {
        animationsRef.current[toast.id] = createToastAnimation();
        setRenderedToasts((current) => [...current, toast]);
        Animated.parallel([
          Animated.timing(animationsRef.current[toast.id].opacity, {
            toValue: 1,
            duration: 180,
            useNativeDriver: true,
          }),
          Animated.timing(animationsRef.current[toast.id].translateY, {
            toValue: 0,
            duration: 180,
            useNativeDriver: true,
          }),
        ]).start();
      }
    });

    renderedToasts.forEach((toast) => {
      if (!nextIds.has(toast.id) && animationsRef.current[toast.id]) {
        Animated.parallel([
          Animated.timing(animationsRef.current[toast.id].opacity, {
            toValue: 0,
            duration: 150,
            useNativeDriver: true,
          }),
          Animated.timing(animationsRef.current[toast.id].translateY, {
            toValue: 16,
            duration: 150,
            useNativeDriver: true,
          }),
        ]).start(() => {
          delete animationsRef.current[toast.id];
          setRenderedToasts((current) => current.filter((item) => item.id !== toast.id));
        });
      }
    });
  }, [renderedToasts, toasts]);

  if (renderedToasts.length === 0) {
    return null;
  }

  return (
    <View pointerEvents="box-none" style={s.container}>
      {renderedToasts.slice(-3).map((toast) => {
        const animation = animationsRef.current[toast.id] || createToastAnimation();
        const { borderColor, Icon } = getToastColors(toast.type);

        return (
          <Animated.View
            key={toast.id}
            style={[
              s.toast,
              { borderColor, opacity: animation.opacity, transform: [{ translateY: animation.translateY }] },
            ]}
          >
            <Icon size={16} color={borderColor} />
            <Text style={s.message}>{toast.message}</Text>
          </Animated.View>
        );
      })}
    </View>
  );
};

const s = StyleSheet.create({
  container: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 100,
    zIndex: 9999,
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
  },
  toast: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    maxWidth: 520,
    width: '100%',
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderRadius: 999,
    backgroundColor: 'rgba(16, 19, 25, 0.92)',
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.22,
    shadowRadius: 18,
    elevation: 10,
  },
  message: {
    flex: 1,
    color: C.text,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
  },
});
