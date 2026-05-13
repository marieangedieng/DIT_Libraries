pipeline {
  agent any

  environment {
    PYTHON_IMAGE = 'python:3.12-slim'
  }

  stages {
    stage('Pipeline Python et DVC') {
      steps {
        sh '''
          echo "Workspace: $PWD"
          git rev-parse --show-toplevel || true
          git status --short || true
          find . -maxdepth 3 -type f -name requirements.txt -print
          test -f services/livres/requirements.txt

          docker run --rm \
            --user "$(id -u):$(id -g)" \
            -e HOME=/tmp \
            -e PIP_CACHE_DIR=/tmp/pip-cache \
            -e PIP_DEFAULT_TIMEOUT=120 \
            -e PIP_RETRIES=10 \
            -v dit_librairie_pip_cache:/tmp/pip-cache \
            --volumes-from "$HOSTNAME" \
            -w "$PWD" \
            "$PYTHON_IMAGE" \
            sh -ec '
              pwd
              test -f services/livres/requirements.txt
              pip_install() {
                python -m pip install --user --retries 10 --timeout 120 --progress-bar off "$@"
              }
              pip_install -r services/livres/requirements.txt
              pip_install -r services/utilisateurs/requirements.txt
              pip_install -r services/emprunts/requirements.txt
              pip_install -r services/statistiques/requirements.txt
              pip_install -r services/recommandation/requirements.txt
              python scripts/preprocess.py
              python scripts/train.py
              python scripts/evaluate.py
            '
        '''
      }
    }

    stage('Build Docker') {
      steps {
        sh 'docker compose --profile prod build'
      }
    }
  }
}
