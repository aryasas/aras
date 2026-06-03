import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, DevSettings, Linking } from 'react-native';
import { theme } from '../lib/theme';

const C = theme.arc.dark;

type Props = {
  children: React.ReactNode;
};

type State = {
  hasError: boolean;
  error: Error | null;
};

// claude-sonnet-4-6
export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  // claude-sonnet-4-6
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  // claude-sonnet-4-6
  handleReload = async () => {
    if (typeof DevSettings?.reload === 'function') {
      DevSettings.reload();
      return;
    }
    await Linking.openURL('aras://');
  };

  // claude-sonnet-4-6
  render() {
    if (this.state.hasError) {
      return (
        <View style={s.root}>
          <Text style={s.code}>ERR_APP_BOUNDARY</Text>
          <Text style={s.title}>Something went wrong</Text>
          <Text style={s.message}>{this.state.error?.message || 'Unexpected application error.'}</Text>
          <TouchableOpacity style={s.button} activeOpacity={0.85} onPress={this.handleReload}>
            <Text style={s.buttonText}>Reload app</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return this.props.children;
  }
}

const s = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.bg,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  code: {
    color: C.text3,
    fontFamily: 'Menlo',
    fontSize: 12,
    letterSpacing: 1.6,
    marginBottom: 10,
  },
  title: {
    color: C.text,
    fontSize: 24,
    fontWeight: '700',
    textAlign: 'center',
  },
  message: {
    color: C.text2,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginTop: 10,
  },
  button: {
    marginTop: 22,
    height: 40,
    paddingHorizontal: 16,
    borderRadius: 10,
    backgroundColor: theme.arc.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    color: theme.arc.accentInk,
    fontSize: 13,
    fontWeight: '700',
  },
});
