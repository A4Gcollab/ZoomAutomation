export default function NotFound() {
    return (
        <div className="flex min-h-screen items-center justify-center bg-background p-4">
            <div className="max-w-md rounded-lg border bg-card p-6 text-center shadow-lg">
                <h2 className="mb-2 text-4xl font-bold">404</h2>
                <h3 className="mb-2 text-xl font-semibold">Page Not Found</h3>
                <p className="mb-4 text-muted-foreground">
                    The page you're looking for doesn't exist or has been moved.
                </p>
                <a
                    href="/"
                    className="inline-block rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
                >
                    Go Home
                </a>
            </div>
        </div>
    );
}
