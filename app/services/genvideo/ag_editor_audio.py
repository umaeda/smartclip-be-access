import math
import os
import random
from typing import List
from moviepy import vfx, afx
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip, TextClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import CrossFadeIn
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.audio.AudioClip import CompositeAudioClip
import tempfile
from pydub import AudioSegment

class EditorAudio:
    """
    Agente de Edição de Vídeo que aplica efeitos (zoom, transições, legendas)
    e gera um arquivo final a partir de imagens e áudio.
    """

    def __init__(self):
        """
        Inicializa o EditorVideo com dimensões padrão para o vídeo.
        """
        self.pasta_destino = "./narracao/"

    def remixar_estilo_reflexao(self, narracao, identificador):
        audio_r = AudioFileClip(narracao)
        audio = self.adicionar_efeito_voz_profunda(audio_r, octaves=-0.05)
        audio = self.adicionar_reverb_pydub(audio, delay_ms=30, decay=0.2, repetitions=5)
        # Usar caminho absoluto para o arquivo de música
        musica_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "emotional-piano-music-256262.mp3")
        audio = self.adicionar_musica_fundo_audio(audio, musica_path=musica_path, volume=0.1, fade_duration=3)

        if not os.path.exists(self.pasta_destino):
            os.makedirs(self.pasta_destino)

        output = os.path.join(self.pasta_destino, f"{identificador}_remix.mp3")

        audio.write_audiofile(output)
        return output

    def adicionar_musica_fundo_audio(self, audio_clip: AudioFileClip, musica_path: str,
                                     volume: float = 0.3, fade_duration: float = 1.0) -> CompositeAudioClip:
        """
        Adiciona música de fundo ao áudio original, mesclando a narração com o áudio de fundo
        e aplicando um fade-out nos últimos segundos.

        O áudio de fundo é recortado para ter a mesma duração do áudio principal e seu volume é reduzido
        conforme o parâmetro 'volume'. Em seguida, ambos os áudios são compostos usando CompositeAudioClip e
        é aplicado um fade-out com a duração especificada.

        Parâmetros:
            audio_clip: AudioFileClip original (por exemplo, a narração já processada com outros efeitos).
            musica_path: Caminho para o arquivo de música de fundo (ex.: 'musicas/fundo.mp3').
            volume: Fator de volume para a música de fundo (padrão: 0.3, ou 30% do volume original).
            fade_duration: Duração do fade-out a ser aplicado nos últimos segundos do áudio (em segundos, padrão: 1.0).

        Retorna:
            CompositeAudioClip: Áudio resultante da composição do áudio original com a música de fundo,
                                  com o fade-out aplicado.
        """
        # Carrega a música de fundo e ajusta sua duração para a do áudio principal
        background_audio = AudioFileClip(musica_path).subclipped(0, audio_clip.duration)
        # Reduz o volume da música de fundo
        background_audio = background_audio.with_effects([afx.MultiplyVolume(volume)])

        # Combina o áudio original com o áudio de fundo
        fade_out = afx.AudioFadeOut(duration=fade_duration)

        final_audio = background_audio.with_effects([fade_out])

        final_audio = CompositeAudioClip([audio_clip, final_audio])
        # Aplica o fade-out nos últimos segundos do áudio composto

        return final_audio


    def adicionar_efeito_voz_profunda(self, audio_clip: AudioFileClip, octaves: float = -0.1) -> AudioFileClip:
        """
        Aplica um efeito para deixar a voz mais profunda, reduzindo o pitch da narração.

        O efeito é realizado alterando a taxa de amostragem do áudio:
            - Uma nova taxa é calculada com base no parâmetro `octaves`.
            - O áudio é reamostrado para a taxa original, mantendo a duração.

        Parâmetros:
            audio_clip: AudioFileClip original.
            octaves: Alteração do pitch em oitavas (padrão: -0.1).
                     Valores negativos reduzem o pitch (voz mais profunda).

        Retorna:
            AudioFileClip com o efeito de voz profunda aplicado.
        """
        # Exporta o áudio original para um arquivo temporário
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            temp_audio_path = temp_audio_file.name
            audio_clip.write_audiofile(temp_audio_path, logger=None)

        # Carrega o áudio com pydub
        audio_segment = AudioSegment.from_file(temp_audio_path, format="wav")

        # Calcula a nova taxa de amostragem para reduzir o pitch
        new_sample_rate = int(audio_segment.frame_rate * (2.0 ** octaves))

        # Aplica a mudança de pitch criando uma nova instância com a taxa alterada
        audio_segment_shifted = audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_sample_rate})

        # Reamostra para a taxa original para manter a duração
        audio_segment_shifted = audio_segment_shifted.set_frame_rate(audio_segment.frame_rate)

        # Salva o áudio processado em um novo arquivo temporário
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file_out:
            temp_audio_path_out = temp_audio_file_out.name
            audio_segment_shifted.export(temp_audio_path_out, format="wav")

        # Reimporta o áudio processado no MoviePy
        audio_clip_shifted = AudioFileClip(temp_audio_path_out)

        return audio_clip_shifted

    def adicionar_reverb_pydub(self, audio_clip: AudioFileClip, delay_ms: int = 50, decay: float = 0.6, repetitions: int = 10) -> AudioFileClip:
        """
        Aplica um efeito de reverberação ao áudio utilizando o pydub.

        O efeito é simulado ao sobrepor múltiplas cópias do áudio original,
        cada uma atrasada por um intervalo fixo (delay_ms) e com volume reduzido
        progressivamente de acordo com o parâmetro 'decay'. O parâmetro 'repetitions'
        define quantas cópias (ou ecos) serão adicionadas.

        Parâmetros:
            audio_clip: AudioFileClip original.
            delay_ms: Atraso em milissegundos para cada repetição (padrão: 50ms).
            decay: Fator de redução de volume para cada eco (0 < decay < 1, padrão: 0.6).
                   Exemplo: 0.6 significa que cada eco terá 60% do volume do eco anterior.
            repetitions: Número de ecos (repetições) a serem sobrepostos (padrão: 10).

        Retorna:
            AudioFileClip com o efeito de reverberação aplicado.
        """
        # Exporta o áudio original para um arquivo temporário (WAV)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            temp_audio_path = temp_audio_file.name
            audio_clip.write_audiofile(temp_audio_path, logger=None)

        # Carrega o áudio usando pydub
        original_segment = AudioSegment.from_file(temp_audio_path, format="wav")

        # Inicializa a saída com o áudio original
        output_segment = original_segment

        # Sobrepõe cópias atrasadas e com volume reduzido
        for i in range(1, repetitions + 1):
            # Calcula a redução de ganho em decibéis para o eco atual.
            # A redução total para o i-ésimo eco é: 20 * log10(decay ** i) = 20 * i * log10(decay)
            gain_reduction = 20 * i * math.log10(decay)
            # Aplica a redução de ganho
            delayed_segment = original_segment.apply_gain(gain_reduction)
            # Sobrepõe a cópia atrasada na posição correspondente
            output_segment = output_segment.overlay(delayed_segment, position=i * delay_ms)

        # Salva o áudio processado em um novo arquivo temporário
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file_out:
            temp_audio_path_out = temp_audio_file_out.name
            output_segment.export(temp_audio_path_out, format="wav")

        # Reimporta o áudio processado no MoviePy
        audio_reverb = AudioFileClip(temp_audio_path_out)

        return audio_reverb



# audio_r = AudioFileClip('narracao.mp3')
# x = EditorAudio()
# a = x.adicionar_reverb_pydub(audio_r, delay_ms=30, decay=0.25, repetitions=6)
# a = x.adicionar_efeito_voz_profunda(a, octaves=-0.13)
# a = x.adicionar_musica_fundo_audio(a, "./sounds/please-calm-my-mind-125566.mp3", volume=0.2, fade_duration=0.5)
# a.write_audiofile('teste3.mp3')



#delay_ms: int = 50,
#decay: float = 0.6,
#repetitions: int = 10) -> AudioFileClip: