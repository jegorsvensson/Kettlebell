import './globals.css';

export const metadata = {
  title: 'Infinite Canvas OS',
  description: 'MVP for Infinite Canvas OS'
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sv">
      <body>{children}</body>
    </html>
  );
}
