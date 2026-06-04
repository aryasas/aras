// claude-sonnet-4-6
import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  CheckCircle2,
  ChevronDown,
  CreditCard,
  Minus,
  Package,
  Plus,
  Search,
  ShoppingCart,
  Store,
  X,
} from 'lucide-react-native';
import { MobileShell } from '../components/MobileShell';
import { haptic } from '../lib/haptics';
import api from '../lib/api';
import { theme } from '../lib/theme';

const C = theme.arc.dark;

type SessionRecord = {
  id: string | number;
  number?: string;
  name?: string;
  label?: string;
  status?: string;
  terminal_name?: string;
  mode?: string;
};

type ProductRecord = {
  id: string | number;
  name?: string;
  code?: string;
  price?: number;
  qty_on_hand?: number;
};

type PaymentModeRecord = {
  id: string | number;
  name?: string;
  label?: string;
};

type CartItem = {
  item: ProductRecord;
  qty: number;
};

// claude-sonnet-4-6
function extractItems<T>(payload: any): T[] {
  if (Array.isArray(payload)) {
    return payload as T[];
  }

  if (Array.isArray(payload?.items)) {
    return payload.items as T[];
  }

  if (Array.isArray(payload?.data)) {
    return payload.data as T[];
  }

  return [];
}

// claude-sonnet-4-6
function formatRp(n: number): string {
  return `Rp ${Math.round(n).toLocaleString('id-ID')}`;
}

// claude-sonnet-4-6
function getSessionLabel(session: SessionRecord): string {
  return session.label || session.name || session.number || `Session #${session.id}`;
}

// claude-sonnet-4-6
function getProductLabel(product: ProductRecord): string {
  return product.name || product.code || `Item #${product.id}`;
}

// claude-sonnet-4-6
function getProductPrice(product: ProductRecord): number {
  return Number(product.price ?? 0);
}

// claude-sonnet-4-6
function getProductStock(product: ProductRecord): number {
  return Number(product.qty_on_hand ?? 0);
}

// claude-sonnet-4-6
function cartItemKey(item: ProductRecord): string {
  return String(item.id);
}

// claude-sonnet-4-6
const SkeletonTile = () => (
  <View style={{ flex: 1, margin: 4, borderRadius: 10, backgroundColor: C.surface2, height: 90 }} />
);

// claude-sonnet-4-6
export const PosScreen = ({ route, navigation }: any) => {
  const initialSessionId = route?.params?.sessionId ?? null;
  const initialSessionLabel = route?.params?.sessionLabel || '';
  const sessionMode = route?.params?.sessionMode || 'sales';
  const [selectedSessionId, setSelectedSessionId] = useState<string | number | null>(initialSessionId);
  const [selectedSessionLabel, setSelectedSessionLabel] = useState(initialSessionLabel);
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [products, setProducts] = useState<ProductRecord[]>([]);
  const [paymentModes, setPaymentModes] = useState<PaymentModeRecord[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [search, setSearch] = useState('');
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [checkoutVisible, setCheckoutVisible] = useState(false);
  const [selectedMode, setSelectedMode] = useState<string | number | null>(null);
  const [amountPaid, setAmountPaid] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // claude-sonnet-4-6
  useEffect(() => {
    if (initialSessionId === null) {
      loadOpenSessions();
      return;
    }

    loadCatalog(initialSessionId);
  }, [initialSessionId]);

  // claude-sonnet-4-6
  const loadOpenSessions = async () => {
    try {
      setLoadingSessions(true);
      const filters = encodeURIComponent(JSON.stringify([{ field: 'status', op: 'not in', value: ['Posted', 'Cancelled'] }]));
      const response = await api.get(`/pot/sessions?page=1&page_size=25&filters=${filters}`);
      setSessions(extractItems<SessionRecord>(response.data));
    } catch (error) {
      console.error('Failed to load POS sessions', error);
      Alert.alert('POS', 'Unable to load open sessions.');
    } finally {
      setLoadingSessions(false);
    }
  };

  // claude-sonnet-4-6
  const loadCatalog = async (sessionId: string | number) => {
    try {
      setLoadingCatalog(true);
      const [itemsResponse, paymentModesResponse] = await Promise.all([
        api.get(`/pot/sessions/${sessionId}/items?mode=sales`),
        api.get('/settings/payment-modes?page=1&page_size=100'),
      ]);

      setProducts(extractItems<ProductRecord>(itemsResponse.data));
      setPaymentModes(extractItems<PaymentModeRecord>(paymentModesResponse.data));
    } catch (error) {
      console.error('Failed to load POS catalog', error);
      Alert.alert('POS', 'Unable to load products or payment modes.');
    } finally {
      setLoadingCatalog(false);
    }
  };

  // claude-sonnet-4-6
  const selectSession = (session: SessionRecord) => {
    setSelectedSessionId(session.id);
    setSelectedSessionLabel(getSessionLabel(session));
    setCart([]);
    setSearch('');
    setSelectedMode(null);
    setAmountPaid('');
    setCheckoutVisible(false);
    loadCatalog(session.id);
  };

  // claude-sonnet-4-6
  const addToCart = (product: ProductRecord) => {
    haptic.light();
    const stock = getProductStock(product);
    if (stock <= 0) {
      haptic.error();
      return;
    }
    setCart((current) => {
      const key = cartItemKey(product);
      const existing = current.find((entry) => cartItemKey(entry.item) === key);
      if (existing) {
        if (existing.qty >= stock) {
          haptic.error();
          return current;
        }
        return current.map((entry) => (
          cartItemKey(entry.item) === key ? { ...entry, qty: entry.qty + 1 } : entry
        ));
      }

      return [...current, { item: product, qty: 1 }];
    });
  };

  // claude-sonnet-4-6
  const changeQty = (product: ProductRecord, delta: number) => {
    const stock = getProductStock(product);
    setCart((current) => {
      const key = cartItemKey(product);
      return current
        .map((entry) => {
          if (cartItemKey(entry.item) !== key) {
            return entry;
          }

          if (delta > 0 && entry.qty >= stock) {
            haptic.error();
            return entry;
          }

          return { ...entry, qty: entry.qty + delta };
        })
        .filter((entry) => entry.qty > 0);
    });
  };

  // claude-sonnet-4-6
  const clearCart = () => {
    setCart([]);
    setSelectedMode(null);
    setAmountPaid('');
  };

  // claude-sonnet-4-6
  const submitInvoice = async () => {
    const activeSessionId = selectedSessionId ?? initialSessionId;
    if (activeSessionId === null) {
      Alert.alert('POS', 'Select an open session first.');
      return;
    }

    if (selectedMode === null || !amountPaid || submitting) {
      return;
    }

    const parsedAmountPaid = parseFloat(amountPaid);
    const payload = {
      items: cart.map((entry) => ({
        item_id: entry.item.id,
        qty: entry.qty,
        unit_price: getProductPrice(entry.item),
      })),
      payment_mode_id: selectedMode,
      amount_paid: parsedAmountPaid,
      mode: sessionMode,
    };

    try {
      setSubmitting(true);
      const response = await api.post(`/pot/sessions/${activeSessionId}/quick_invoice`, payload);
      const { invoice_number, change_amount } = response.data?.data || response.data || {};
      const changeText = Number(change_amount) > 0 ? `\nChange: ${formatRp(Number(change_amount))}` : '';
      haptic.success();
      Alert.alert(
        'Invoice Created',
        `${invoice_number || 'Invoice'}${changeText}`,
        [{ text: 'OK' }]
      );
      clearCart();
      setCheckoutVisible(false);
    } catch (error: any) {
      console.error('Failed to submit POS invoice', error);
      Alert.alert('POS', error?.message || 'Unable to create invoice.');
    } finally {
      setSubmitting(false);
    }
  };

  const resolvedTitle = selectedSessionLabel || initialSessionLabel || 'POS';
  const filteredProducts = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return products;
    }

    return products.filter((product) => {
      const name = getProductLabel(product).toLowerCase();
      const code = String(product.code || '').toLowerCase();
      return name.includes(query) || code.includes(query);
    });
  }, [products, search]);

  const cartTotal = useMemo(() => {
    return cart.reduce((sum, entry) => sum + getProductPrice(entry.item) * entry.qty, 0);
  }, [cart]);

  const cartMap = useMemo(() => {
    const map = new Map<string, number>();
    cart.forEach((entry) => {
      map.set(cartItemKey(entry.item), entry.qty);
    });
    return map;
  }, [cart]);

  const amountPaidValue = Number.parseFloat(amountPaid);
  const changeAmount = Number.isFinite(amountPaidValue) ? amountPaidValue - cartTotal : 0;

  return (
    <MobileShell active="items" title={resolvedTitle} navigation={navigation}>
      <View style={styles.root}>
        <View style={styles.topPanel}>
          {selectedSessionId === null ? (
            <View style={styles.sessionPicker}>
              <View style={styles.sessionHeader}>
                <Store size={18} color={C.text3} />
                <Text style={styles.sectionTitle}>Open Sessions</Text>
              </View>

              {loadingSessions ? (
                <View style={styles.centerState}>
                  <ActivityIndicator color={theme.arc.accent} />
                </View>
              ) : sessions.length === 0 ? (
                <View style={styles.emptySessionState}>
                  <Text style={styles.emptySessionText}>No open POS sessions. Open a session from the web app first.</Text>
                </View>
              ) : (
                <ScrollView contentContainerStyle={styles.sessionList} showsVerticalScrollIndicator={false}>
                  {sessions.map((session) => (
                    <TouchableOpacity
                      key={String(session.id)}
                      style={styles.sessionCard}
                      activeOpacity={0.85}
                      onPress={() => selectSession(session)}
                    >
                      <View style={styles.sessionCardTop}>
                        <Text style={styles.sessionLabel}>{getSessionLabel(session)}</Text>
                        <ChevronDown size={16} color={C.text3} style={{ transform: [{ rotate: '-90deg' }] }} />
                      </View>
                      <Text style={styles.sessionMeta}>{session.mode || session.status || 'Open session'}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              )}
            </View>
          ) : (
            <>
              <View style={styles.searchRow}>
                <Search size={16} color={C.text3} />
                <TextInput
                  value={search}
                  onChangeText={setSearch}
                  placeholder="Search product name or code"
                  placeholderTextColor={C.text3}
                  autoCapitalize="none"
                  autoCorrect={false}
                  style={styles.searchInput}
                />
              </View>

              {loadingCatalog ? (
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12 }}>
                  {Array.from({ length: 6 }).map((_, index) => (
                    <SkeletonTile key={index} />
                  ))}
                </View>
              ) : (
                <FlatList
                  data={filteredProducts}
                  numColumns={2}
                  columnWrapperStyle={{ paddingHorizontal: 12 }}
                  contentContainerStyle={styles.gridContent}
                  keyExtractor={(item) => String(item.id)}
                  renderItem={({ item }) => {
                    const stock = getProductStock(item);
                    const active = Boolean(cartMap.get(cartItemKey(item)));
                    const dimmed = stock <= 0;
                    return (
                      <TouchableOpacity
                        activeOpacity={0.85}
                        onPress={() => addToCart(item)}
                        style={[
                          styles.productCard,
                          active && styles.productCardActive,
                          dimmed && styles.productCardDimmed,
                        ]}
                      >
                        <View style={styles.productCardTop}>
                          <View style={styles.productBadge}>
                            <Text style={styles.productBadgeText}>{dimmed ? 'Out' : `Stock ${stock}`}</Text>
                          </View>
                          <Text style={styles.productCode} numberOfLines={1}>
                            {item.code || 'No code'}
                          </Text>
                        </View>
                        <Text style={styles.productName} numberOfLines={2}>
                          {getProductLabel(item)}
                        </Text>
                        <Text style={styles.productPrice}>{formatRp(getProductPrice(item))}</Text>
                        {active && (
                          <View style={styles.activeTag}>
                            <CheckCircle2 size={12} color={theme.arc.accent} />
                            <Text style={styles.activeTagText}>In cart</Text>
                          </View>
                        )}
                      </TouchableOpacity>
                    );
                  }}
                  ListEmptyComponent={(
                    <View style={styles.noProductsState}>
                      <Package size={22} color={C.text3} />
                      <Text style={styles.noProductsText}>No matching products.</Text>
                    </View>
                  )}
                  showsVerticalScrollIndicator={false}
                />
              )}
            </>
          )}
        </View>

        <View style={styles.bottomPanel}>
          <View style={styles.cartHeader}>
            <ShoppingCart size={18} color={C.text3} />
            <Text style={styles.sectionTitle}>Cart</Text>
            <Text style={styles.cartCount}>{cart.length}</Text>
          </View>

          {cart.length === 0 ? (
            <View style={styles.emptyCartState}>
              <Text style={styles.emptyCartText}>
                {selectedSessionId === null ? 'Select a session to start selling.' : 'No items yet. Tap a product to add it.'}
              </Text>
            </View>
          ) : (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.cartStrip}
            >
              {cart.map((entry) => (
                <View key={cartItemKey(entry.item)} style={styles.cartItemCard}>
                  <Text style={styles.cartItemName} numberOfLines={2}>
                    {getProductLabel(entry.item)}
                  </Text>
                  <Text style={styles.cartItemPrice}>{formatRp(getProductPrice(entry.item))}</Text>
                  <View style={styles.qtyRow}>
                    <TouchableOpacity
                      style={styles.qtyButton}
                      activeOpacity={0.85}
                      onPress={() => changeQty(entry.item, -1)}
                    >
                      <Minus size={14} color={C.text} />
                    </TouchableOpacity>
                    <Text style={styles.qtyValue}>{entry.qty}</Text>
                    <TouchableOpacity
                      style={styles.qtyButton}
                      activeOpacity={0.85}
                      onPress={() => changeQty(entry.item, 1)}
                    >
                      <Plus size={14} color={C.text} />
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </ScrollView>
          )}

          <View style={styles.totalRow}>
            <View>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={styles.totalValue}>{formatRp(cartTotal)}</Text>
            </View>
            <TouchableOpacity
              style={[styles.checkoutButton, cart.length === 0 && styles.checkoutButtonDisabled]}
              activeOpacity={0.85}
              disabled={cart.length === 0}
              onPress={() => setCheckoutVisible(true)}
            >
              <Text style={styles.checkoutButtonText}>Checkout</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <Modal animationType="slide" visible={checkoutVisible} onRequestClose={() => setCheckoutVisible(false)}>
        <View style={styles.checkoutRoot}>
          <View style={styles.checkoutHeader}>
            <View>
              <Text style={styles.checkoutKicker}>Checkout</Text>
              <Text style={styles.checkoutTitle}>{resolvedTitle}</Text>
            </View>
            <TouchableOpacity
              style={styles.closeButton}
              activeOpacity={0.85}
              onPress={() => setCheckoutVisible(false)}
            >
              <X size={16} color={C.text} />
            </TouchableOpacity>
          </View>

          <ScrollView contentContainerStyle={styles.checkoutContent} keyboardShouldPersistTaps="handled">
            <View style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>Order summary</Text>
              {cart.map((entry) => (
                <View key={cartItemKey(entry.item)} style={styles.summaryRow}>
                  <Text style={styles.summaryName} numberOfLines={1}>
                    {getProductLabel(entry.item)} x{entry.qty}
                  </Text>
                  <Text style={styles.summaryValue}>{formatRp(getProductPrice(entry.item) * entry.qty)}</Text>
                </View>
              ))}
              <View style={styles.summaryDivider} />
              <View style={styles.summaryRow}>
                <Text style={styles.summaryTotalLabel}>Total</Text>
                <Text style={styles.summaryTotalValue}>{formatRp(cartTotal)}</Text>
              </View>
            </View>

            <View style={styles.pillSection}>
              <Text style={styles.pillTitle}>Payment mode</Text>
              <View style={styles.pillWrap}>
                {paymentModes.map((mode) => {
                  const modeLabel = mode.label || mode.name || `Mode ${mode.id}`;
                  const active = selectedMode === mode.id;
                  return (
                    <TouchableOpacity
                      key={String(mode.id)}
                      style={[styles.paymentPill, active && styles.paymentPillActive]}
                      activeOpacity={0.85}
                      onPress={() => setSelectedMode(mode.id)}
                    >
                      <Text style={[styles.paymentPillText, active && styles.paymentPillTextActive]}>
                        {modeLabel}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>

            <View style={styles.amountSection}>
              <Text style={styles.inputLabel}>Amount paid</Text>
              <View style={styles.amountInputWrap}>
                <CreditCard size={16} color={C.text3} />
                <TextInput
                  value={amountPaid}
                  onChangeText={setAmountPaid}
                  placeholder="0"
                  placeholderTextColor={C.text3}
                  keyboardType="decimal-pad"
                  style={styles.amountInput}
                />
              </View>
            </View>

            <View style={styles.changeCard}>
              <Text style={styles.changeLabel}>Change</Text>
              <Text style={styles.changeValue}>{formatRp(changeAmount)}</Text>
            </View>

            <TouchableOpacity
              style={[
                styles.confirmButton,
                (selectedMode === null || !amountPaid || submitting) && styles.confirmButtonDisabled,
              ]}
              activeOpacity={0.85}
              disabled={selectedMode === null || !amountPaid || submitting}
              onPress={submitInvoice}
            >
              <Text style={styles.confirmButtonText}>
                {submitting ? 'Submitting...' : 'Confirm'}
              </Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </Modal>
    </MobileShell>
  );
};

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.bg,
  },
  topPanel: {
    flex: 6,
    paddingTop: 12,
  },
  bottomPanel: {
    flex: 4,
    borderTopWidth: 1,
    borderTopColor: C.line,
    backgroundColor: C.surface,
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 110,
  },
  sectionTitle: {
    color: C.text,
    fontSize: 15,
    fontWeight: '700',
  },
  centerState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sessionPicker: {
    flex: 1,
    paddingHorizontal: 12,
  },
  sessionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  sessionList: {
    gap: 10,
    paddingBottom: 10,
  },
  sessionCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    gap: 4,
  },
  sessionCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  sessionLabel: {
    color: C.text,
    fontSize: 15,
    fontWeight: '700',
    flex: 1,
  },
  sessionMeta: {
    color: C.text3,
    fontSize: 12,
  },
  emptySessionState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  emptySessionText: {
    color: C.text3,
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 19,
  },
  searchRow: {
    marginHorizontal: 12,
    marginBottom: 12,
    height: 42,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    color: C.text,
    fontSize: 14,
  },
  gridContent: {
    paddingBottom: 14,
  },
  productCard: {
    flex: 1,
    marginBottom: 12,
    marginHorizontal: 6,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    gap: 8,
    minHeight: 142,
  },
  productCardActive: {
    borderColor: theme.arc.accent,
  },
  productCardDimmed: {
    opacity: 0.45,
  },
  productCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  productBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
    backgroundColor: C.surface2,
  },
  productBadgeText: {
    color: C.text3,
    fontSize: 10,
    fontWeight: '700',
  },
  productCode: {
    flex: 1,
    color: C.text3,
    fontFamily: 'Menlo',
    fontSize: 10,
    textAlign: 'right',
  },
  productName: {
    color: C.text,
    fontSize: 14,
    fontWeight: '700',
    lineHeight: 19,
  },
  productPrice: {
    color: theme.arc.accent,
    fontSize: 14,
    fontWeight: '700',
  },
  activeTag: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: 'rgba(232, 155, 108, 0.35)',
    backgroundColor: 'rgba(232, 155, 108, 0.08)',
  },
  activeTagText: {
    color: theme.arc.accent,
    fontSize: 10,
    fontWeight: '700',
  },
  noProductsState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 30,
    gap: 10,
  },
  noProductsText: {
    color: C.text3,
    fontSize: 13,
  },
  cartHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  cartCount: {
    marginLeft: 'auto',
    color: C.text3,
    fontSize: 12,
    fontWeight: '700',
    fontFamily: 'Menlo',
  },
  emptyCartState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24,
  },
  emptyCartText: {
    color: C.text3,
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 19,
  },
  cartStrip: {
    gap: 10,
    paddingBottom: 12,
  },
  cartItemCard: {
    width: 180,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.bg,
    gap: 8,
  },
  cartItemName: {
    color: C.text,
    fontSize: 13.5,
    fontWeight: '700',
    lineHeight: 18,
  },
  cartItemPrice: {
    color: C.text3,
    fontSize: 12,
  },
  qtyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  qtyButton: {
    width: 30,
    height: 30,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  qtyValue: {
    minWidth: 24,
    color: C.text,
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'center',
  },
  totalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 'auto',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: C.line,
  },
  totalLabel: {
    color: C.text3,
    fontSize: 11,
    fontFamily: 'Menlo',
    letterSpacing: 1.1,
    textTransform: 'uppercase',
  },
  totalValue: {
    marginTop: 2,
    color: C.text,
    fontSize: 18,
    fontWeight: '700',
  },
  checkoutButton: {
    minWidth: 120,
    height: 42,
    borderRadius: 10,
    backgroundColor: theme.arc.accent,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  checkoutButtonDisabled: {
    opacity: 0.45,
  },
  checkoutButtonText: {
    color: theme.arc.accentInk,
    fontSize: 14,
    fontWeight: '700',
  },
  checkoutRoot: {
    flex: 1,
    backgroundColor: C.bg,
    paddingTop: 18,
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  checkoutHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 16,
    marginBottom: 18,
  },
  checkoutKicker: {
    color: C.text3,
    fontFamily: 'Menlo',
    fontSize: 11,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  checkoutTitle: {
    marginTop: 4,
    color: C.text,
    fontSize: 24,
    fontWeight: '700',
  },
  closeButton: {
    width: 34,
    height: 34,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkoutContent: {
    paddingBottom: 24,
    gap: 14,
  },
  summaryCard: {
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    gap: 10,
  },
  summaryTitle: {
    color: C.text,
    fontSize: 15,
    fontWeight: '700',
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 16,
  },
  summaryName: {
    flex: 1,
    color: C.text,
    fontSize: 13,
  },
  summaryValue: {
    color: C.text,
    fontSize: 13,
    fontWeight: '700',
  },
  summaryDivider: {
    height: 1,
    backgroundColor: C.line,
  },
  summaryTotalLabel: {
    color: C.text3,
    fontSize: 12,
    fontFamily: 'Menlo',
    textTransform: 'uppercase',
  },
  summaryTotalValue: {
    color: C.text,
    fontSize: 16,
    fontWeight: '700',
  },
  pillSection: {
    gap: 10,
  },
  pillTitle: {
    color: C.text,
    fontSize: 14,
    fontWeight: '700',
  },
  pillWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  paymentPill: {
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
  },
  paymentPillActive: {
    borderColor: theme.arc.accent,
    backgroundColor: 'rgba(232, 155, 108, 0.12)',
  },
  paymentPillText: {
    color: C.text,
    fontSize: 13,
    fontWeight: '700',
  },
  paymentPillTextActive: {
    color: theme.arc.accent,
  },
  amountSection: {
    gap: 8,
  },
  inputLabel: {
    color: C.text,
    fontSize: 14,
    fontWeight: '700',
  },
  amountInputWrap: {
    height: 44,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    gap: 8,
  },
  amountInput: {
    flex: 1,
    color: C.text,
    fontSize: 14,
  },
  changeCard: {
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    gap: 4,
  },
  changeLabel: {
    color: C.text3,
    fontSize: 11,
    fontFamily: 'Menlo',
    letterSpacing: 1.1,
    textTransform: 'uppercase',
  },
  changeValue: {
    color: C.text,
    fontSize: 20,
    fontWeight: '700',
  },
  confirmButton: {
    height: 46,
    borderRadius: 10,
    backgroundColor: theme.arc.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 6,
  },
  confirmButtonDisabled: {
    opacity: 0.5,
  },
  confirmButtonText: {
    color: theme.arc.accentInk,
    fontSize: 14,
    fontWeight: '700',
  },
});
