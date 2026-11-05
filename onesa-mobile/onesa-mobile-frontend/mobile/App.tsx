import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import {
  SafeAreaProvider,
  SafeAreaView,
  useSafeAreaInsets,
} from "react-native-safe-area-context";
import * as SecureStore from "expo-secure-store";
import * as Crypto from "expo-crypto";
import * as WebBrowser from "expo-web-browser";
import * as Sharing from "expo-sharing";
import { File, Paths } from "expo-file-system";
import PreviewApp from "./src/PreviewApp";
import {
  apiBase,
  ApiError,
  base64Url,
  callbackParameters,
  compactCache,
  request,
  type Account,
  type Credential,
  type Item,
} from "./src/api";
import {
  BrandMark,
  Button,
  Card,
  DetailRow,
  Label,
  SectionHeading,
  Tag,
  colors,
  styles,
} from "./src/ui";

const configuration = (() => {
  try {
    return {
      base: apiBase(process.env.EXPO_PUBLIC_API_BASE_URL, __DEV__),
      error: null,
    };
  } catch {
    return {
      base: null,
      error:
        "The account service address needs to be configured for this build.",
    };
  }
})();
const tabs = ["Home", "Application", "Help", "Account"] as const;
type Tab = (typeof tabs)[number];
const plans = [
  ["everyday", "Everyday"],
  ["reach", "Reach"],
  ["family-farm", "Family & Farm"],
] as const;
const human = (value: unknown) =>
  String(value ?? "Not recorded").replaceAll("_", " ");
function Field({
  label,
  value,
  onChange,
  multiline = false,
  password = false,
}: {
  label: string;
  value: string;
  onChange: (s: string) => void;
  multiline?: boolean;
  password?: boolean;
}) {
  return (
    <View style={local.field}>
      <Text style={styles.strongBody}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        value={value}
        onChangeText={onChange}
        style={[local.input, multiline && local.textarea]}
        secureTextEntry={password}
        autoCapitalize="none"
        autoCorrect={!password}
        multiline={multiline}
        maxLength={multiline ? 1200 : password ? 256 : 100}
        textAlignVertical={multiline ? "top" : "center"}
      />
    </View>
  );
}
function Choice({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly (readonly [string, string])[];
  value: string;
  onChange: (s: string) => void;
}) {
  return (
    <View style={local.field}>
      <Text style={styles.strongBody}>{label}</Text>
      <View style={local.choices}>
        {options.map(([id, title]) => (
          <Pressable
            key={id}
            onPress={() => onChange(id)}
            accessibilityRole="radio"
            accessibilityState={{ checked: value === id }}
            style={[local.choice, value === id && local.selected]}
          >
            <Text style={styles.strongBody}>{title}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}
function MobileAccount({ openPreview }: { openPreview: () => void }) {
  const insets = useSafeAreaInsets();
  const [tab, setTab] = useState<Tab>("Home"),
    [storageKey, setStorageKey] = useState<string | null>(null),
    [credential, setCredential] = useState<Credential | null>(null),
    [account, setAccount] = useState<Account | null>(null);
  const [authMode, setAuthMode] = useState<"lab" | "onesa" | null>(null),
    [ssoAvailable, setSsoAvailable] = useState(false),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [cached, setCached] = useState<Record<string, unknown> | null>(null),
    [lastFetched, setLastFetched] = useState("");
  const [username, setUsername] = useState(""),
    [password, setPassword] = useState(""),
    [displayName, setDisplayName] = useState(""),
    [area, setArea] = useState(""),
    [deviceModel, setDeviceModel] = useState(""),
    [planId, setPlanId] = useState("everyday"),
    [simFormat, setSimFormat] = useState("physical"),
    [consent, setConsent] = useState(false);
  const [category, setCategory] = useState("other"),
    [subject, setSubject] = useState(""),
    [message, setMessage] = useState(""),
    [replyId, setReplyId] = useState<string | null>(null),
    [reply, setReply] = useState(""),
    [requestType, setRequestType] = useState("sim_replacement"),
    [requestDetail, setRequestDetail] = useState("");
  const current = useRef<Credential | null>(null),
    requestKeys = useRef(new Map<string, string>()),
    callbackCodes = useRef(new Set<string>()),
    generation = useRef(0);
  const base = configuration.base;
  const clearLocal = useCallback(async () => {
    generation.current++;
    current.current = null;
    setCredential(null);
    setAccount(null);
    setCached(null);
    setLastFetched("");
    requestKeys.current.clear();
    if (storageKey)
      await Promise.all([
        SecureStore.deleteItemAsync(storageKey),
        SecureStore.deleteItemAsync(storageKey + ".cache"),
        SecureStore.deleteItemAsync(storageKey + ".flow"),
      ]);
  }, [storageKey]);
  const saveCredential = useCallback(
    async (value: Credential) => {
      if (!storageKey || !base)
        throw Error("The account service is not configured.");
      if (
        !/^[A-Za-z0-9_-]{43}$/.test(value.token) ||
        !value.user?.subject ||
        !Number.isFinite(value.user.expiresAt) ||
        value.user.expiresAt * 1000 <= Date.now()
      )
        throw Error("The service returned an invalid session.");
      generation.current++;
      await SecureStore.deleteItemAsync(storageKey + ".cache");
      await SecureStore.setItemAsync(storageKey, JSON.stringify(value), {
        keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
      });
      current.current = value;
      setCredential(value);
      setCached(null);
      setAccount(null);
      setPassword("");
      setError("");
    },
    [storageKey, base],
  );
  const refresh = useCallback(
    async (value: Credential | null = current.current) => {
      if (!base || !value) return;
      const run = generation.current;
      setLoading(true);
      try {
        const data = await request<Account>(base, "/v1/me", {
          token: value.token,
        });
        if (
          run !== generation.current ||
          current.current?.token !== value.token
        )
          return;
        if (data.profile?.subject !== value.user.subject)
          throw Error("The account response did not match this session.");
        setAccount(data);
        setLastFetched(new Date().toISOString());
        setError("");
        const snapshot = compactCache(data);
        setCached(snapshot as Record<string, unknown>);
        if (storageKey)
          await SecureStore.setItemAsync(
            storageKey + ".cache",
            JSON.stringify(snapshot),
            { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY },
          );
      } catch (e) {
        if (run !== generation.current) return;
        if (e instanceof ApiError && e.status === 401) await clearLocal();
        setError(
          e instanceof Error ? e.message : "Unable to refresh your account.",
        );
      } finally {
        if (run === generation.current) setLoading(false);
      }
    },
    [base, storageKey, clearLocal],
  );
  useEffect(() => {
    let alive = true;
    void (async () => {
      if (!base) {
        setLoading(false);
        return;
      }
      try {
        const hash = await Crypto.digestStringAsync(
            Crypto.CryptoDigestAlgorithm.SHA256,
            base,
          ),
          key = "onesa.mobile.v1." + hash.slice(0, 24);
        if (!alive) return;
        setStorageKey(key);
        const [stored, previous, session] = await Promise.all([
          SecureStore.getItemAsync(key),
          SecureStore.getItemAsync(key + ".cache"),
          request<{ authMode: "lab" | "onesa"; ssoAvailable: boolean }>(
            base,
            "/v1/session",
          ).catch(() => null),
        ]);
        if (!alive) return;
        if (session) {
          setAuthMode(session.authMode);
          setSsoAvailable(session.ssoAvailable);
        }
        if (stored) {
          const value = JSON.parse(stored) as Credential;
          if (
            value.user?.expiresAt * 1000 > Date.now() &&
            /^[A-Za-z0-9_-]{43}$/.test(value.token)
          ) {
            current.current = value;
            setCredential(value);
            if (previous) {
              const parsed = JSON.parse(previous);
              if (parsed.subject === value.user.subject) setCached(parsed);
            }
          } else
            await Promise.all([
              SecureStore.deleteItemAsync(key),
              SecureStore.deleteItemAsync(key + ".cache"),
            ]);
        }
        if (!session)
          setError(
            "The account service is unavailable. Saved information may be out of date.",
          );
      } catch {
        if (alive)
          setError(
            "Secure account storage could not be opened. Please try again.",
          );
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
      generation.current++;
    };
  }, [base]);
  useEffect(() => {
    if (credential && storageKey) void refresh(credential);
  }, [credential, storageKey, refresh]);
  const run = async (action: () => Promise<void>) => {
    if (busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "The operation could not be completed.",
      );
    } finally {
      setBusy(false);
    }
  };
  const completeNative = useCallback(
    async (url: string) => {
      if (!base || !storageKey) return;
      const callbackCode = new URL(url).searchParams.get("code");
      if (callbackCode && callbackCodes.current.has(callbackCode)) return;
      const raw = await SecureStore.getItemAsync(storageKey + ".flow");
      if (!raw) throw Error("Start sign-in again on this device.");
      const flow = JSON.parse(raw) as {
        state: string;
        verifier: string;
        expires: number;
      };
      if (flow.expires < Date.now())
        throw Error("This sign-in expired. Start again.");
      const result = callbackParameters(url, flow.state);
      if (callbackCodes.current.has(result.code)) return;
      callbackCodes.current.add(result.code);
      try {
        const issued = await request<{
          token: string;
          user: Credential["user"];
        }>(base, "/v1/auth/onesa/native/exchange", {
          method: "POST",
          body: { ...result, verifier: flow.verifier },
        });
        await saveCredential(issued);
        await SecureStore.deleteItemAsync(storageKey + ".flow");
        setTab("Home");
      } catch (e) {
        callbackCodes.current.delete(result.code);
        throw e;
      }
    },
    [base, storageKey, saveCredential],
  );
  useEffect(() => {
    if (!storageKey) return;
    const handler = ({ url }: { url: string }) => {
      if (url.startsWith("onesamobile://auth/callback"))
        void completeNative(url).catch((e) =>
          setError(e instanceof Error ? e.message : "Sign-in failed."),
        );
    };
    const listener = Linking.addEventListener("url", handler);
    void Linking.getInitialURL().then((url) => {
      if (url) handler({ url });
    });
    return () => listener.remove();
  }, [storageKey, completeNative]);
  const signIn = () =>
    run(async () => {
      if (!base) return;
      const result = await request<{ token: string; user: Credential["user"] }>(
        base,
        "/v1/session/login",
        {
          method: "POST",
          body: {
            username,
            password,
            surface: "customer",
            transport: "bearer",
          },
        },
      );
      await saveCredential(result);
      setTab("Home");
    });
  const signInOnesa = () =>
    run(async () => {
      if (!base || !storageKey) return;
      const state = base64Url(await Crypto.getRandomBytesAsync(32)),
        verifier = base64Url(await Crypto.getRandomBytesAsync(32)),
        challenge = (
          await Crypto.digestStringAsync(
            Crypto.CryptoDigestAlgorithm.SHA256,
            verifier,
            { encoding: Crypto.CryptoEncoding.BASE64 },
          )
        )
          .replaceAll("+", "-")
          .replaceAll("/", "_")
          .replaceAll("=", "");
      await SecureStore.setItemAsync(
        storageKey + ".flow",
        JSON.stringify({ state, verifier, expires: Date.now() + 600000 }),
        { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY },
      );
      const url = new URL(base + "/v1/auth/onesa/start");
      url.searchParams.set("surface", "customer");
      url.searchParams.set("codeChallenge", challenge);
      url.searchParams.set("state", state);
      const result = await WebBrowser.openAuthSessionAsync(
        url.href,
        "onesamobile://auth/callback",
      );
      if (result.type === "success") await completeNative(result.url);
      else setNotice("Sign-in cancelled. No account change was made.");
    });
  const signOut = () =>
    run(async () => {
      const previous = current.current;
      await clearLocal();
      setTab("Home");
      if (previous && base) {
        try {
          await request(base, "/v1/session/logout", {
            method: "POST",
            token: previous.token,
          });
          setNotice("Signed out on this device.");
        } catch {
          setNotice(
            "Signed out on this device. The service could not confirm remote session revocation.",
          );
        }
      }
    });
  const mutate = async (
    path: string,
    body: unknown,
    success: string,
    method: "POST" | "PATCH" = "POST",
  ) => {
    const user = current.current;
    if (!base || !user) throw Error("Sign in first.");
    const signature = method + path + JSON.stringify(body);
    let key = requestKeys.current.get(signature);
    if (!key) {
      key = Crypto.randomUUID();
      requestKeys.current.set(signature, key);
    }
    try {
      await request(base, path, { token: user.token, method, body, key });
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) await clearLocal();
      else if (e instanceof ApiError && e.status === 409) await refresh(user);
      throw e;
    }
    requestKeys.current.delete(signature);
    if (current.current?.token !== user.token) return;
    await refresh(user);
    setNotice(success);
  };
  const shareDocument = (item?: Item) =>
    run(async () => {
      const user = current.current;
      if (!user || !base) return;
      if (!(await Sharing.isAvailableAsync()))
        throw Error("Document sharing is unavailable on this device.");
      const file = new File(
        Paths.cache,
        "onesa-mobile-" + Crypto.randomUUID() + (item ? ".pdf" : ".json"),
      );
      try {
        if (item) {
          if (!/^[a-f0-9-]{36}$/.test(item.id))
            throw Error("Invalid document reference.");
          await File.downloadFileAsync(
            base + "/v1/documents/" + item.id + ".pdf",
            file,
            { headers: { Authorization: "Bearer " + user.token } },
          );
        } else {
          await File.downloadFileAsync(base + "/v1/me/export", file, {
            headers: { Authorization: "Bearer " + user.token },
          });
        }
        await Sharing.shareAsync(file.uri, {
          mimeType: item ? "application/pdf" : "application/json",
          dialogTitle: item
            ? "Share your test receipt"
            : "Export your account records",
        });
      } finally {
        if (file.exists) file.delete();
      }
    });
  const loadMore = (kind: "tickets" | "ledger" | "requests") =>
    run(async () => {
      const user = current.current,
        cursor = account?.cursors?.[kind];
      if (!base || !user || !cursor) return;
      const page = await request<{
        items: Item[];
        nextCursor: string | null;
        total: number;
      }>(base, "/v1/me/records/" + kind, {
        token: user.token,
        query: { cursor, limit: 50 },
      });
      if (current.current?.token !== user.token) return;
      setAccount((previous) =>
        previous
          ? {
              ...previous,
              [kind]: [
                ...new Map(
                  [...previous[kind], ...page.items].map((item) => [
                    item.id,
                    item,
                  ]),
                ).values(),
              ],
              cursors: { ...previous.cursors, [kind]: page.nextCursor },
              counts: { ...previous.counts, [kind]: page.total },
            }
          : previous,
      );
    });
  const application =
    account?.applications.find((a) => a.state !== "declined") ??
    account?.applications[0];
  const beginCorrection = () => {
    if (!application) return;
    setDisplayName(String(application.displayName));
    setArea(String(application.area));
    setDeviceModel(String(application.deviceModel));
    setPlanId(String(application.planId));
    setSimFormat(String(application.simFormat));
    setConsent(false);
    setTab("Application");
  };
  const submitApplication = () =>
    run(async () => {
      if (!consent) throw Error("Confirm the pilot consent before submitting.");
      const input = {
        displayName,
        area,
        deviceModel,
        planId,
        simFormat,
        consentToPilot: true,
      };
      const existing =
        application &&
        ["review_required", "information_required"].includes(
          String(application.state),
        );
      await mutate(
        existing ? "/v1/applications/" + application.id : "/v1/applications",
        existing ? { ...input, revision: application.revision } : input,
        "Your pilot application was saved. Mobile service remains unavailable.",
        existing ? "PATCH" : "POST",
      );
      setTab("Home");
    });
  const canEdit =
    !!account &&
    (!application ||
      ["review_required", "information_required", "declined"].includes(
        String(application.state),
      ));
  return (
    <SafeAreaView style={styles.root} edges={["top", "left", "right"]}>
      <StatusBar style="dark" />
      <View style={[styles.frame, styles.header]}>
        <View style={styles.wordmark} accessibilityLabel="Onesa Mobile">
          <BrandMark />
          <View>
            <Text style={styles.brand}>onesa</Text>
            <Text style={styles.brandQualifier}>mobile</Text>
          </View>
        </View>
        <Text style={styles.headerTag}>
          {credential ? "MY ACCOUNT" : "WELCOME"}
        </Text>
      </View>
      <View style={styles.demoBanner}>
        <View style={styles.frame}>
          <Text style={styles.demoText}>
            {authMode === "lab" || credential?.user.source === "lab"
              ? "Hardware pilot lab · no commercial mobile service"
              : "Service preparation · availability subject to approved partners"}
          </Text>
        </View>
      </View>
      <ScrollView
        key={tab}
        style={styles.scroll}
        contentContainerStyle={[styles.frame, styles.content]}
        keyboardShouldPersistTaps="handled"
        contentInsetAdjustmentBehavior="automatic"
      >
        {error ? (
          <View accessibilityRole="alert" style={local.error}>
            <Text style={local.errorText}>{error}</Text>
          </View>
        ) : null}
        {notice ? (
          <Text accessibilityLiveRegion="polite" style={local.notice}>
            {notice}
          </Text>
        ) : null}
        {busy || loading ? (
          <ActivityIndicator
            accessibilityLabel="Loading account"
            color={colors.forest}
          />
        ) : null}
        {!credential ? (
          <>
            <SectionHeading>Your mobile account</SectionHeading>
            <Card>
              <Text style={styles.body}>
                See your application, get help and keep your account records in
                one place.
              </Text>
              {configuration.error ? (
                <Text style={styles.body}>{configuration.error}</Text>
              ) : null}
              {!base ? (
                <Text style={styles.body}>
                  Account access is not configured for this build. You can
                  explore the product preview.
                </Text>
              ) : authMode === "lab" ? (
                <>
                  <Tag>ISOLATED LAB SIGN-IN</Tag>
                  <Text style={styles.small}>
                    Use an administrator-issued test customer account. Keep real
                    identity documents and payment details out of the lab.
                  </Text>
                  <Field
                    label="Lab username"
                    value={username}
                    onChange={setUsername}
                  />
                  <Field
                    label="Lab password"
                    value={password}
                    onChange={setPassword}
                    password
                  />
                  <Button
                    onPress={signIn}
                    disabled={busy || !username || !password}
                  >
                    Sign in to the lab
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    onPress={signInOnesa}
                    disabled={busy || !ssoAvailable}
                  >
                    Continue with Onesa
                  </Button>
                  <Text style={styles.small}>
                    Registration, password recovery and account verification
                    take place in the shared Onesa sign-in service.
                  </Text>
                  {!ssoAvailable ? (
                    <Text style={styles.small}>
                      Account sign-in is awaiting configuration.
                    </Text>
                  ) : null}
                </>
              )}
              <Button secondary onPress={openPreview}>
                Explore without signing in
              </Button>
            </Card>
          </>
        ) : (
          <>
            {tab === "Home" ? (
              <>
                <SectionHeading>
                  Hello, {credential.user.displayName}
                </SectionHeading>
                <Card>
                  <View style={styles.cardTitleRow}>
                    <Text style={styles.cardHeading}>Your service</Text>
                    <Tag tone="amber">NOT PROVISIONED</Tag>
                  </View>
                  <DetailRow
                    label="Application"
                    value={
                      application
                        ? human(application.state)
                        : account
                          ? "Not submitted"
                          : "Waiting for refresh"
                    }
                  />
                  <DetailRow
                    label="Plan concept"
                    value={
                      application
                        ? human(application.planId)
                        : account
                          ? "Not selected"
                          : "Waiting for refresh"
                    }
                  />
                  <DetailRow label="Usage" value="Available after activation" />
                  <Text style={styles.small}>
                    {lastFetched
                      ? "Account checked " +
                        new Date(lastFetched).toLocaleString()
                      : cached
                        ? "Saved account information from " +
                          new Date(String(cached.savedAt)).toLocaleString() +
                          ". Reconnect to refresh."
                        : "Waiting for the account service."}
                  </Text>
                  <Button
                    secondary
                    onPress={() => void run(() => refresh())}
                    disabled={busy}
                  >
                    Refresh account
                  </Button>
                </Card>
                <Card>
                  <SectionHeading>Next step</SectionHeading>
                  <Text style={styles.body}>
                    {!account
                      ? "Reconnect and refresh your account to see the latest next step."
                      : !application
                        ? "Submit a pilot application to record your device and SIM preference."
                        : application.state === "information_required"
                          ? String(
                              application.reviewNote ??
                                "Update the information requested by the team.",
                            )
                          : application.state === "awaiting_host"
                            ? "Your pilot review is recorded. Activation requires an authorized host connection."
                            : application.state === "declined"
                              ? String(
                                  application.reviewNote ??
                                    "The pilot application was declined. You can ask support or submit another application.",
                                )
                              : "The team will review your pilot application."}
                  </Text>
                  {canEdit ? (
                    <Button
                      onPress={
                        application
                          ? beginCorrection
                          : () => setTab("Application")
                      }
                    >
                      {application
                        ? "Review your details"
                        : "Start pilot application"}
                    </Button>
                  ) : (
                    <Button onPress={() => setTab("Help")}>
                      Contact support
                    </Button>
                  )}
                </Card>
                <Card>
                  <SectionHeading>
                    Connectivity, clearly explained
                  </SectionHeading>
                  <Text style={styles.body}>
                    Direct-to-cell connects an eligible handset through an
                    authorized satellite mobile network. A Starlink dish
                    provides a separate Wi-Fi path. This app does not detect or
                    switch your phone onto a satellite.
                  </Text>
                  <Text style={styles.small}>
                    Messaging, data and calls require separate device and
                    service qualification.
                  </Text>
                </Card>
              </>
            ) : null}
            {tab === "Application" ? (
              <>
                <SectionHeading>Pilot application</SectionHeading>
                <Text style={styles.body}>
                  Plan concepts are not approved offers for sale. Submitting
                  this form does not activate a SIM or verify registration.
                </Text>
                {!canEdit ? (
                  <Card>
                    <DetailRow
                      label="Status"
                      value={human(application?.state)}
                    />
                    <Text style={styles.body}>
                      Contact support to request a change while the application
                      is with the host review queue.
                    </Text>
                    <Button onPress={() => setTab("Help")}>Ask for help</Button>
                  </Card>
                ) : (
                  <Card>
                    <Field
                      label="Test display name"
                      value={displayName}
                      onChange={setDisplayName}
                    />
                    <Field label="Pilot area" value={area} onChange={setArea} />
                    <Field
                      label="Device model"
                      value={deviceModel}
                      onChange={setDeviceModel}
                    />
                    <Choice
                      label="Plan concept"
                      options={plans}
                      value={planId}
                      onChange={setPlanId}
                    />
                    <Choice
                      label="SIM preference"
                      options={[
                        ["physical", "Physical SIM"],
                        ["esim", "eSIM"],
                      ]}
                      value={simFormat}
                      onChange={setSimFormat}
                    />
                    <View style={local.consent}>
                      <Switch
                        accessibilityLabel="I understand this is a pilot application"
                        value={consent}
                        onValueChange={setConsent}
                        trackColor={{ true: colors.green }}
                      />
                      <Text style={[styles.body, { flex: 1 }]}>
                        I understand this pilot form does not purchase or
                        activate mobile service.
                      </Text>
                    </View>
                    <Button
                      onPress={submitApplication}
                      disabled={
                        busy ||
                        !consent ||
                        !displayName.trim() ||
                        !area.trim() ||
                        !deviceModel.trim()
                      }
                    >
                      Save pilot application
                    </Button>
                  </Card>
                )}
              </>
            ) : null}
            {tab === "Help" ? (
              <>
                <SectionHeading>How can we help?</SectionHeading>
                <Card>
                  <Choice
                    label="Category"
                    options={[
                      ["registration", "Application"],
                      ["sim", "SIM"],
                      ["coverage", "Coverage"],
                      ["billing", "Billing"],
                      ["other", "Other"],
                    ]}
                    value={category}
                    onChange={setCategory}
                  />
                  <Field
                    label="Subject"
                    value={subject}
                    onChange={setSubject}
                  />
                  <Field
                    label="Message"
                    value={message}
                    onChange={setMessage}
                    multiline
                  />
                  <Button
                    disabled={busy || !subject.trim() || !message.trim()}
                    onPress={() =>
                      void run(async () => {
                        await mutate(
                          "/v1/support/tickets",
                          { category, subject, message },
                          "Your support case was saved.",
                        );
                        setSubject("");
                        setMessage("");
                      })
                    }
                  >
                    Send support request
                  </Button>
                </Card>
                <SectionHeading>Your cases</SectionHeading>
                {!account?.tickets.length ? (
                  <Text style={styles.body}>
                    {account
                      ? "You have no saved support cases."
                      : "Refresh your account to load support cases."}
                  </Text>
                ) : (
                  account.tickets.map((ticket) => (
                    <Card key={ticket.id}>
                      <View style={styles.cardTitleRow}>
                        <Text style={styles.cardHeading}>
                          {String(ticket.subject)}
                        </Text>
                        <Tag>{human(ticket.status)}</Tag>
                      </View>
                      <Text style={styles.body}>{String(ticket.message)}</Text>
                      {Array.isArray(ticket.notes)
                        ? (
                            ticket.notes as {
                              text: string;
                              authorRole: string;
                              at: string;
                            }[]
                          ).map((note, index) => (
                            <View key={index} style={local.reply}>
                              <Text style={styles.strongBody}>
                                {human(note.authorRole)}
                              </Text>
                              <Text style={styles.body}>{note.text}</Text>
                            </View>
                          ))
                        : null}
                      {replyId === ticket.id ? (
                        <>
                          <Field
                            label="Your reply"
                            value={reply}
                            onChange={setReply}
                            multiline
                          />
                          <Button
                            disabled={busy || !reply.trim()}
                            onPress={() =>
                              void run(async () => {
                                await mutate(
                                  "/v1/support/tickets/" +
                                    ticket.id +
                                    "/replies",
                                  { revision: ticket.revision, message: reply },
                                  "Your reply was saved.",
                                );
                                setReply("");
                                setReplyId(null);
                              })
                            }
                          >
                            Send reply
                          </Button>
                        </>
                      ) : (
                        <Button
                          secondary
                          onPress={() => {
                            setReplyId(ticket.id);
                            setReply("");
                          }}
                        >
                          Reply to this case
                        </Button>
                      )}
                    </Card>
                  ))
                )}
                {account?.cursors?.tickets ? (
                  <Button
                    secondary
                    disabled={busy}
                    onPress={() => loadMore("tickets")}
                  >
                    Load older cases
                  </Button>
                ) : null}
              </>
            ) : null}
            {tab === "Account" ? (
              <>
                <SectionHeading>Account and records</SectionHeading>
                <Card>
                  <DetailRow
                    label="Account"
                    value={credential.user.displayName}
                  />
                  <DetailRow
                    label="Session"
                    value={
                      "Expires " +
                      new Date(
                        credential.user.expiresAt * 1000,
                      ).toLocaleTimeString()
                    }
                  />
                  <Text style={styles.small}>
                    Automatic background refresh is off. Documents download only
                    when you request them.
                  </Text>
                  <Button
                    secondary
                    onPress={() => shareDocument()}
                    disabled={busy}
                  >
                    Export my account records
                  </Button>
                  <Button secondary onPress={signOut} disabled={busy}>
                    Sign out
                  </Button>
                </Card>
                <SectionHeading>Test receipts</SectionHeading>
                <Text style={styles.body}>
                  Lab records do not represent a charge or a tax invoice.
                </Text>
                {!account?.ledger.length ? (
                  <Text style={styles.small}>
                    No test receipts have been recorded.
                  </Text>
                ) : (
                  account.ledger.map((entry) => (
                    <Card key={entry.id}>
                      <DetailRow
                        label={String(entry.reference)}
                        value={
                          "USD " + (Number(entry.amountMinor) / 100).toFixed(2)
                        }
                      />
                      <DetailRow label="State" value={human(entry.state)} />
                      <Button
                        secondary
                        onPress={() => shareDocument(entry)}
                        disabled={busy}
                      >
                        Download and share test PDF
                      </Button>
                    </Card>
                  ))
                )}
                {account?.cursors?.ledger ? (
                  <Button
                    secondary
                    disabled={busy}
                    onPress={() => loadMore("ledger")}
                  >
                    Load older receipts
                  </Button>
                ) : null}
                <Card>
                  <SectionHeading>Account requests</SectionHeading>
                  <Choice
                    label="Request type"
                    options={[
                      ["sim_replacement", "SIM replacement"],
                      ["number_porting", "Number transfer"],
                      ["data_correction", "Correct my data"],
                      ["account_closure", "Close account"],
                    ]}
                    value={requestType}
                    onChange={setRequestType}
                  />
                  <Field
                    label="Request details"
                    value={requestDetail}
                    onChange={setRequestDetail}
                    multiline
                  />
                  <Button
                    disabled={busy || !requestDetail.trim()}
                    onPress={() =>
                      void run(async () => {
                        await mutate(
                          "/v1/account/requests",
                          { type: requestType, detail: requestDetail },
                          "Your request is with the team. No automatic account or SIM change was made.",
                        );
                        setRequestDetail("");
                      })
                    }
                  >
                    Submit account request
                  </Button>
                </Card>
                {account?.requests.map((item) => (
                  <Card key={item.id}>
                    <DetailRow
                      label={human(item.type)}
                      value={human(item.status)}
                    />
                    <Text style={styles.body}>
                      {String(item.responseNote ?? item.detail)}
                    </Text>
                  </Card>
                ))}
                {account?.cursors?.requests ? (
                  <Button
                    secondary
                    disabled={busy}
                    onPress={() => loadMore("requests")}
                  >
                    Load older requests
                  </Button>
                ) : null}
              </>
            ) : null}
          </>
        )}
      </ScrollView>
      {credential ? (
        <View
          style={[styles.nav, { paddingBottom: Math.max(insets.bottom, 8) }]}
        >
          <View style={[styles.frame, styles.navInner]}>
            {tabs.map((name) => (
              <Pressable
                key={name}
                accessibilityRole="tab"
                accessibilityState={{ selected: tab === name }}
                onPress={() => setTab(name)}
                style={styles.navItem}
              >
                <View
                  style={[
                    styles.navIndicator,
                    tab === name && styles.navIndicatorActive,
                  ]}
                />
                <Text
                  style={[styles.navText, tab === name && styles.navTextActive]}
                >
                  {name}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>
      ) : null}
    </SafeAreaView>
  );
}
export default function App() {
  const [preview, setPreview] = useState(false);
  return (
    <SafeAreaProvider>
      {preview ? (
        <View style={{ flex: 1 }}>
          <SafeAreaView edges={["top"]}>
            <Button secondary onPress={() => setPreview(false)}>
              Return to account access
            </Button>
          </SafeAreaView>
          <PreviewApp />
        </View>
      ) : (
        <MobileAccount openPreview={() => setPreview(true)} />
      )}
    </SafeAreaProvider>
  );
}
const local = StyleSheet.create({
  field: { gap: 6 },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 11,
    fontSize: 16,
    color: colors.ink,
    backgroundColor: colors.white,
  },
  textarea: { minHeight: 96 },
  choices: { flexDirection: "row", flexWrap: "wrap", gap: 7 },
  choice: {
    minHeight: 44,
    paddingHorizontal: 12,
    paddingVertical: 11,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    justifyContent: "center",
  },
  selected: { backgroundColor: colors.pale, borderColor: colors.forest },
  consent: { flexDirection: "row", alignItems: "center", gap: 10 },
  error: {
    padding: 12,
    borderLeftWidth: 3,
    borderColor: "#AC342C",
    backgroundColor: "#FFF1EE",
  },
  errorText: { color: "#8C241F", fontSize: 14, lineHeight: 21 },
  notice: {
    fontSize: 14,
    lineHeight: 21,
    color: colors.ink,
    padding: 12,
    backgroundColor: colors.pale,
  },
  reply: {
    borderLeftWidth: 2,
    borderColor: colors.border,
    paddingLeft: 10,
    gap: 3,
  },
});
