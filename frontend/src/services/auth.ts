/**
 * Servicio de autenticación con AWS Cognito (Authorization Code Grant + PKCE).
 *
 * Flujo:
 *   1. buildLoginUrl() → genera code_verifier + state + URL del Hosted UI
 *      (guarda code_verifier y state en sessionStorage para el callback)
 *   2. Usuario hace login en Cognito → redirige a /callback?code=...&state=...
 *   3. exchangeCodeForToken() → cambia el code por id_token usando code_verifier
 *   4. setToken() → guarda el id_token en sessionStorage
 *
 * Storage:
 *   - "id_token"             → JWT actual
 *   - "pkce_code_verifier"   → temporal, durante el login flow
 *   - "oauth_state"          → temporal, durante el login flow (CSRF)
 *   - "post_login_redirect"  → temporal, ruta a la que volver tras login
 */

import type { CognitoTokenResponse } from "@/types/api";

// ============================================================
// Constantes desde el entorno
// ============================================================
const DOMAIN = import.meta.env.VITE_COGNITO_DOMAIN;
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID;
const REDIRECT_URI = import.meta.env.VITE_COGNITO_REDIRECT_URI;
const LOGOUT_URI = import.meta.env.VITE_COGNITO_LOGOUT_URI;

// Storage keys (centralizadas para evitar typos)
const STORAGE_KEYS = {
  TOKEN: "id_token",
  CODE_VERIFIER: "pkce_code_verifier",
  STATE: "oauth_state",
  REDIRECT: "post_login_redirect",
} as const;

// ============================================================
// Helpers PKCE / CSRF
// ============================================================

/** Genera bytes aleatorios criptográficamente seguros. */
function randomBytes(length: number): Uint8Array {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return array;
}

/** Codifica bytes a base64url (URL-safe, sin padding). */
function base64UrlEncode(buffer: Uint8Array | ArrayBuffer): string {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  let str = "";
  for (let i = 0; i < bytes.length; i++) {
    str += String.fromCharCode(bytes[i]);
  }
  return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}

/** Crea un code_verifier para PKCE (43-128 chars). 32 bytes → 43 chars base64url. */
function generateCodeVerifier(): string {
  return base64UrlEncode(randomBytes(32));
}

/** Calcula el code_challenge = base64url(SHA256(code_verifier)). */
async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return base64UrlEncode(digest);
}

/** Random state para protección CSRF. */
function generateState(): string {
  return base64UrlEncode(randomBytes(16));
}

// ============================================================
// Storage (JWT y temporales)
// ============================================================
export function getToken(): string | null {
  return sessionStorage.getItem(STORAGE_KEYS.TOKEN);
}

export function setToken(token: string): void {
  sessionStorage.setItem(STORAGE_KEYS.TOKEN, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(STORAGE_KEYS.TOKEN);
}

function clearOAuthTemporaries(): void {
  sessionStorage.removeItem(STORAGE_KEYS.CODE_VERIFIER);
  sessionStorage.removeItem(STORAGE_KEYS.STATE);
  sessionStorage.removeItem(STORAGE_KEYS.REDIRECT);
}

export function getPostLoginRedirect(): string {
  return sessionStorage.getItem(STORAGE_KEYS.REDIRECT) || "/chat";
}

// ============================================================
// Construcción de URLs
// ============================================================

/**
 * Genera la URL del Hosted UI para iniciar sesión.
 * Guarda code_verifier + state en sessionStorage (los lee el callback).
 *
 * @param postLoginRedirect ruta a la que volver tras login exitoso
 */
export async function buildLoginUrl(postLoginRedirect: string): Promise<string> {
  // Crear y guardar los valores temporales del flujo OAuth
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = await generateCodeChallenge(codeVerifier);
  const state = generateState();

  sessionStorage.setItem(STORAGE_KEYS.CODE_VERIFIER, codeVerifier);
  sessionStorage.setItem(STORAGE_KEYS.STATE, state);
  sessionStorage.setItem(STORAGE_KEYS.REDIRECT, postLoginRedirect);

  // Armar la URL
  const params = new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    scope: "openid email profile",
    state,
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
  });

  return `https://${DOMAIN}/login?${params.toString()}`;
}

/**
 * Genera la URL de logout de Cognito.
 * Cognito desloguea (incluso de Google si aplica) y redirige a LOGOUT_URI.
 */
export function buildLogoutUrl(): string {
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    logout_uri: LOGOUT_URI,
  });
  return `https://${DOMAIN}/logout?${params.toString()}`;
}

// ============================================================
// Intercambio code → token
// ============================================================

export class AuthError extends Error {}

/**
 * Intercambia el `code` por tokens.
 * Verifica que el `state` recibido coincide con el guardado (CSRF).
 * Usa el `code_verifier` guardado en sessionStorage (PKCE).
 */
export async function exchangeCodeForToken(
  code: string,
  receivedState: string,
): Promise<string> {
  // --- Verificar state (CSRF) ---
  const expectedState = sessionStorage.getItem(STORAGE_KEYS.STATE);
  if (!expectedState || expectedState !== receivedState) {
    clearOAuthTemporaries();
    throw new AuthError("State inválido (posible CSRF).");
  }

  // --- Recuperar code_verifier ---
  const codeVerifier = sessionStorage.getItem(STORAGE_KEYS.CODE_VERIFIER);
  if (!codeVerifier) {
    clearOAuthTemporaries();
    throw new AuthError("Falta el code_verifier; reinicia el login.");
  }

  // --- POST al endpoint de Cognito ---
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: CLIENT_ID,
    code,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier,
  });

  let response: Response;
  try {
    response = await fetch(`https://${DOMAIN}/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
  } catch (err) {
    throw new AuthError(`Error de red al contactar Cognito: ${String(err)}`);
  }

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new AuthError(
      `Cognito rechazó el code (${response.status}): ${text || "sin detalle"}`,
    );
  }

  const data: CognitoTokenResponse = await response.json();
  if (!data.id_token) {
    throw new AuthError("Respuesta de Cognito sin id_token.");
  }

  // Limpiar temporales (el REDIRECT se mantiene hasta que el AuthContext lo consuma)
  sessionStorage.removeItem(STORAGE_KEYS.CODE_VERIFIER);
  sessionStorage.removeItem(STORAGE_KEYS.STATE);

  return data.id_token;
}

/** Consume y limpia el redirect post-login. */
export function consumePostLoginRedirect(): string {
  const redirect = getPostLoginRedirect();
  sessionStorage.removeItem(STORAGE_KEYS.REDIRECT);
  return redirect;
}
