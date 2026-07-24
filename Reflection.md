Reflection

What assumptions did you make?

During the reverse engineering process, I assumed that the web portal communicated with its backend through HTTP endpoints rather than rendering all data server-side. Based on the observed network traffic, I also assumed that the Better Auth session cookie remained valid for the duration of a client session, allowing authenticated requests without logging in repeatedly. Since the portal did not provide official API documentation, all endpoint behavior was inferred from browser network requests and validated through direct testing.

Which part was the most difficult, and how did you get unstuck?

The most challenging part was understanding the authentication flow. My initial implementation received HTTP 403 Forbidden responses because I attempted to authenticate by sending only a POST request to the login endpoint. To debug this, I inspected the browser's network traffic, request headers, cookies, and login sequence using Chrome Developer Tools. I discovered that the portal used Better Auth with a secure session cookie and that my client needed to replicate the browser's behavior more closely. After updating the HTTP client to preserve cookies and follow the correct authentication flow, I was able to establish a persistent authenticated session and successfully access the protected endpoints.

If you had another day, what would you improve?

With additional time, I would focus on improving the robustness and usability of the project rather than simply adding more endpoints. I would implement automatic session renewal when authentication expires, add retry logic with exponential backoff for transient network failures, and introduce response caching to reduce unnecessary requests to the legacy portal. I would also increase test coverage with integration tests and build a lightweight frontend dashboard that visualizes meter locations, energy consumption trends, and transformer hierarchy using the API.

What mistake did you make while solving this?

My biggest mistake was assuming that the authentication process would be straightforward. I initially focused on reproducing only the login request instead of analyzing the complete authentication workflow used by the browser. This led to repeated 403 responses until I carefully examined the request sequence, cookies, and headers exchanged during login. That experience reinforced the importance of understanding the entire protocol before implementing a client for an undocumented system.

If you were reviewing your own submission, what would you criticise?

If I were reviewing my own submission, I would identify production readiness as the main area for improvement. While the API successfully wraps the legacy portal and provides a cleaner interface, it could benefit from more comprehensive automated tests, stronger error handling, structured logging, and monitoring. Features such as configurable caching, rate limiting, Docker support, and CI/CD would make the project more maintainable and scalable. These improvements were intentionally left out to prioritize completing the core reverse engineering task and delivering a functional API within the available time.
