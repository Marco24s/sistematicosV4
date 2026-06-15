import os
import sys
import subprocess
import time

def run_unified_server():
    print("\033[1;32m============================================================\033[0m")
    print("\033[1;32m   SIMA :: SERVIDOR UNIFICADO AERONAVAL (NALCOMIS)         \033[0m")
    print("\033[1;32m============================================================\033[0m")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")
    venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    out_dir = os.path.join(frontend_dir, "out")

    # Validar entorno virtual
    if not os.path.exists(venv_python):
        print("\033[1;33m[ERROR] No se detectó el entorno virtual en .venv\\Scripts\\python.exe\033[0m")
        sys.exit(1)

    # Si no existe la carpeta compilada 'out', compilarla ahora
    if not os.path.exists(out_dir):
        print("\033[1;33m[SISTEMA] No se detectó compilación previa del frontend. Compilando...\033[0m")
        build_proc = subprocess.run("npm run build", cwd=frontend_dir, shell=True)
        if build_proc.returncode != 0:
            print("\033[1;31m[ERROR] Error al compilar el frontend. Abortando.\033[0m")
            sys.exit(1)

    print("\033[1;32m[OK] Frontend estático verificado.\033[0m")
    print("\033[1;32m[INICIO] Levanto Servidor Unificado FastAPI (Puerto 8000)...\033[0m")

    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = backend_dir

    backend_process = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
        cwd=root_dir,
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print("\033[1;32m------------------------------------------------------------\033[0m")
    print("\033[1;32m SISTEMA OPERATIVO Y DISPONIBLE DESDE URL ÚNICA EN:          \033[0m")
    print("\033[1;32m ▶ http://localhost:8000                                    \033[0m")
    print("\033[1;32m------------------------------------------------------------\033[0m")
    print("\033[1;33m Presione CTRL+C para detener el servidor de manera segura. \033[0m")

    try:
        while True:
            line = backend_process.stdout.readline()
            if line:
                print(f"\033[32m[SISTEMA]\033[0m {line.strip()}")
            if backend_process.poll() is not None:
                print("\033[1;31m[ALERTA] El servidor unificado se detuvo.\033[0m")
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\033[1;33m\n[SISTEMA] Cerrando puertos y apagando servidor...\033[0m")
    finally:
        try:
            backend_process.terminate()
            backend_process.wait(timeout=2)
        except Exception:
            pass
        print("\033[1;32m[SIMA] Servidor unificado apagado con éxito.\033[0m")

if __name__ == "__main__":
    run_unified_server()
