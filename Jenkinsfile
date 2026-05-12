pipeline {
  agent any

  environment {
    PYTHON_IMAGE = 'python:3.12-slim'
  }

  stages {
    stage('Pipeline Python et DVC') {
      steps {
        sh '''
          docker run --rm \
            --user "$(id -u):$(id -g)" \
            -e HOME=/tmp \
            -e PIP_CACHE_DIR=/tmp/pip-cache \
            -v "$PWD:/workspace" \
            -w /workspace \
            "$PYTHON_IMAGE" \
            sh -ec '
              python -m pip install --user --upgrade pip
              python -m pip install --user -r services/livres/requirements.txt
              python -m pip install --user -r services/utilisateurs/requirements.txt
              python -m pip install --user -r services/emprunts/requirements.txt
              python -m pip install --user -r services/statistiques/requirements.txt
              python -m pip install --user -r services/recommandation/requirements.txt
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
