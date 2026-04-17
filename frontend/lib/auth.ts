import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

const googleConfigured = Boolean(
  process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET,
);

const providers = googleConfigured
  ? [
      Google({
        clientId: process.env.GOOGLE_CLIENT_ID ?? "",
        clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
        authorization: {
          params: {
            access_type: "offline",
            prompt: "consent",
            scope:
              "openid email profile https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
          },
        },
      }),
    ]
  : [];

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
  secret: process.env.NEXTAUTH_SECRET,
  session: {
    strategy: "jwt",
  },
  providers,
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.expiresAt = account.expires_at;
        token.scope = account.scope;
      }

      return token;
    },
    async session({ session, token }) {
      session.accessToken = typeof token.accessToken === "string" ? token.accessToken : undefined;
      session.scope = typeof token.scope === "string" ? token.scope : undefined;
      session.providerReady = googleConfigured;
      return session;
    },
  },
});

export function getAuthConfigurationSummary() {
  return {
    googleConfigured,
    nextAuthSecretConfigured: Boolean(process.env.NEXTAUTH_SECRET),
  };
}
