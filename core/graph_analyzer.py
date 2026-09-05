import sympy as sp


class GraphAnalyzer:
    """
    تحليل رياضي للدوال قبل رسمها.
    لا يقوم بالرسم؛ مهمته استخراج المعلومات المهمة فقط.
    """

    def __init__(self, expression):
        self.x = sp.Symbol("x")

        self.expr = sp.sympify(
            str(expression),
            locals={
                "x": self.x,
                "sin": sp.sin,
                "cos": sp.cos,
                "tan": sp.tan,
                "sqrt": sp.sqrt,
                "log": sp.log,
                "ln": sp.log,
                "exp": sp.exp,
                "pi": sp.pi,
                "e": sp.E,
            },
        )

    def analyze(self):
        return {
            "expression": str(self.expr),
            "roots": self.find_roots(),
            "y_intercept": self.find_y_intercept(),
            "critical_points": self.find_critical_points(),
            "asymptotes": self.find_asymptotes(),
        }

    def find_roots(self):
        """
        إيجاد الجذور الحقيقية ضمن مجال الرسم.
        
        نستخدم الحل الرمزي أولاً، ثم فحصًا عدديًا محدودًا
        لالتقاط الجذور الدورية مثل جذور sin(x) و cos(x).
        """
        roots = []

        # --------------------------------------------------------
        # 1. Symbolic roots
        # --------------------------------------------------------
        try:
            symbolic_roots = sp.solve(
                sp.Eq(self.expr, 0),
                self.x
            )

            for root in symbolic_roots:
                if root.is_real is False:
                    continue

                try:
                    value = float(sp.N(root))

                    if -10 <= value <= 10:
                        roots.append(value)

                except (TypeError, ValueError, OverflowError):
                    continue

        except Exception:
            pass

        # --------------------------------------------------------
        # 2. Numerical scan
        # --------------------------------------------------------
        # هذا مهم للدوال الدورية مثل:
        # sin(x) -> -pi, 0, pi
        # cos(x) -> -pi/2, pi/2
        #
        # نستخدم مجال الرسم الحالي تقريبًا [-10, 10].
        # لا نستخدم solve() بشكل مكثف حتى يبقى الأداء مناسبًا
        # على Termux / Android.
        try:
            import math

            fn = sp.lambdify(
                self.x,
                self.expr,
                "math"
            )

            xmin = -10.0
            xmax = 10.0
            samples = 2001

            previous_x = None
            previous_y = None

            for i in range(samples):
                xv = xmin + (xmax - xmin) * i / (samples - 1)

                try:
                    yv = float(fn(xv))

                    if not math.isfinite(yv):
                        previous_x = None
                        previous_y = None
                        continue

                except Exception:
                    previous_x = None
                    previous_y = None
                    continue

                if previous_x is not None and previous_y is not None:
                    # جذر مباشر
                    if yv == 0:
                        roots.append(xv)

                    # تغير الإشارة = يوجد جذر بين النقطتين
                    elif (
                        previous_y * yv < 0
                        and abs(previous_y) < 20
                        and abs(yv) < 20
                    ):
                        left = previous_x
                        right = xv
                        f_left = previous_y

                        # Bisection
                        for _ in range(40):
                            mid = (left + right) / 2

                            try:
                                f_mid = float(fn(mid))

                                if not math.isfinite(f_mid):
                                    break

                            except Exception:
                                break

                            if abs(f_mid) < 1e-10:
                                left = mid
                                right = mid
                                break

                            if f_left * f_mid <= 0:
                                right = mid
                            else:
                                left = mid
                                f_left = f_mid

                        roots.append((left + right) / 2)

                previous_x = xv
                previous_y = yv

        except Exception:
            pass

        # --------------------------------------------------------
        # 3. Remove duplicates
        # --------------------------------------------------------
        unique_roots = []

        for value in sorted(roots):
            if not unique_roots or abs(value - unique_roots[-1]) > 1e-5:
                unique_roots.append(value)

        return unique_roots

    def find_y_intercept(self):
        """إيجاد تقاطع الدالة مع محور y."""
        try:
            value = self.expr.subs(self.x, 0)

            if value.is_real is False or value in (
                sp.zoo,
                sp.oo,
                -sp.oo,
            ):
                return None

            return float(sp.N(value))

        except Exception:
            return None

    def find_critical_points(self):
        """إيجاد النقاط الحرجة حيث المشتقة تساوي صفرًا."""
        try:
            derivative = sp.diff(self.expr, self.x)
            roots = sp.solve(sp.Eq(derivative, 0), self.x)

            points = []

            for root in roots:
                if root.is_real is False:
                    continue

                try:
                    x_value = float(sp.N(root))
                    y_value = float(sp.N(self.expr.subs(self.x, root)))

                    if (
                        abs(x_value) <= 1000
                        and abs(y_value) <= 1000
                    ):
                        points.append(
                            {
                                "x": x_value,
                                "y": y_value,
                            }
                        )

                except (TypeError, ValueError, OverflowError):
                    continue

            return points

        except Exception:
            return []

    def find_asymptotes(self):
        """كشف المقاربات الرأسية والأفقية الأساسية."""
        result = {
            "vertical": [],
            "horizontal": [],
        }

        # المقاربات الرأسية من أصفار المقام / singularities
        try:
            denominator = sp.denom(sp.together(self.expr))

            if denominator != 1:
                candidates = sp.solve(
                    sp.Eq(denominator, 0),
                    self.x,
                )

                for candidate in candidates:
                    if candidate.is_real is False:
                        continue

                    try:
                        value = float(sp.N(candidate))
                        if abs(value) <= 1000:
                            result["vertical"].append(value)
                    except (TypeError, ValueError):
                        continue

        except Exception:
            pass

        # --------------------------------------------------------
        # Special handling for tan(x)
        # --------------------------------------------------------
        # tan(x) has vertical asymptotes at:
        # x = pi/2 + k*pi
        #
        # نضيف فقط المقاربات الموجودة داخل مجال الرسم [-10, 10].
        try:
            if self.expr.has(sp.tan):
                k_min = int(
                    sp.ceiling(
                        (-10 - sp.pi / 2) / sp.pi
                    )
                )

                k_max = int(
                    sp.floor(
                        (10 - sp.pi / 2) / sp.pi
                    )
                )

                for k in range(k_min, k_max + 1):
                    candidate = sp.pi / 2 + k * sp.pi

                    try:
                        value = float(sp.N(candidate))

                        if -10 <= value <= 10:
                            result["vertical"].append(value)

                    except (TypeError, ValueError, OverflowError):
                        continue

        except Exception:
            pass

        # المقاربة الأفقية عند +∞ و -∞
        for direction, key in [
            (sp.oo, "+infinity"),
            (-sp.oo, "-infinity"),
        ]:
            try:
                limit = sp.limit(
                    self.expr,
                    self.x,
                    direction,
                )

                if limit.is_real and limit not in (
                    sp.oo,
                    -sp.oo,
                    sp.zoo,
                ):
                    value = float(sp.N(limit))

                    if key == "+infinity":
                        result["horizontal"].append(
                            {
                                "direction": "+infinity",
                                "y": value,
                            }
                        )
                    else:
                        result["horizontal"].append(
                            {
                                "direction": "-infinity",
                                "y": value,
                            }
                        )

            except Exception:
                continue

        # إزالة التكرار
        result["vertical"] = sorted(
            set(result["vertical"])
        )

        unique_horizontal = []
        seen = set()

        for item in result["horizontal"]:
            marker = (
                item["direction"],
                item["y"],
            )

            if marker not in seen:
                seen.add(marker)
                unique_horizontal.append(item)

        result["horizontal"] = unique_horizontal

        return result


def analyze_function(expression):
    """
    واجهة بسيطة للاستخدام من باقي المشروع.
    """
    return GraphAnalyzer(expression).analyze()
