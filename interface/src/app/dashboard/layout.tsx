import { BloombergLayout } from "@/components/dashboard/bloomberg-layout";

export default function Layout({ children }: { children: React.ReactNode }) {
    return <BloombergLayout>{children}</BloombergLayout>;
}
